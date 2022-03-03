import glob
import json
import os
from lxml import etree
from jinja2 import Environment, FileSystemLoader, select_autoescape
from .schemavalidator import validate_XML
from lxml.isoschematron import Schematron
import jsonlines

env = Environment(
    loader=FileSystemLoader('config/templates'),
    autoescape=select_autoescape([ 'xml'])
)

def dpc_files(pattern):
    LIST = glob.glob(pattern, recursive = True)
    for dpc_file in LIST:
        dataset_name = os.path.basename(os.path.dirname(dpc_file))
        yield (dataset_name, dpc_file)

def _load_dpc_file(dpc_file):
    with open(dpc_file, encoding='utf-8') as fc:
        return json.load(fc) 

def _load_linked_data(dpc_file):
    return _load_dpc_file(dpc_file)['ld+json']

def _replace_env_vars(value):
    if value and value.startswith('$DPC_'):
        return os.environ.get(value[1:])

def dpcs(pattern):
    for (dataset_name, dpc_file) in dpc_files(pattern):
        # open dpc file
        with open(dpc_file, encoding='utf-8') as fc:
            data = json.load(fc)
            yield (dataset_name, data)
    
def download_links(pattern):
    for (dataset_name, data) in dpcs(pattern):
        if data.get('downloadUrl'):
            yield (dataset_name, data['downloadUrl'], data.get('downloadCert'), data['fileType'])

def datasets_with_schematron_validation(pattern):
    for (dataset_name, dpc_file) in dpc_files(pattern):
        # open dpc file
        with open(dpc_file, encoding='utf-8') as fc:
            data = json.load(fc)
            if data.get('fileType')=='xml' and data.get('schematron'):
                yield (dataset_name, data['schematron'])

def datasets_out_files(pattern, outdir, out_file_pattern):
    for (dataset_name, dpc_file) in dpc_files(pattern):
        LIST = glob.glob(outdir + dataset_name + "/" + out_file_pattern)
        yield (dataset_name, LIST)

def _format_for(encodingFormat):
    # FIXME this is temporary and should be replaced, e.g. by using datapackage's format metainfo
    if encodingFormat == "text/csv":
        return "csv"
    elif encodingFormat == "text/xml":
        return "xml"
    elif encodingFormat == "application/json":
        return "json"
    elif encodingFormat == "application/zip":
        return "zip"
    return "unknown"


def _enhanced_linked_data(ld, dataset_name, image_url, dpc_host):
    dataset = ld.copy()
    dataset['image'] = image_url if image_url else  f'https://{dpc_host}/img/data.jpg'
    landing_page = f'https://{dpc_host}/{dataset_name}/index.html'
    dataset['landingPage'] = landing_page
    dataset['datapackageName'] = dataset_name.lower()
    # FIXME this is temporary and should be replaced, e.g. by using datapackage's format metainfo
    dataset['format'] = _format_for(ld['distribution'][0]['encodingFormat'])
    
    return dataset
    

def render_index(basedir, dpc_host, index_file, sitemap_file):
    '''Render the landing page and sitemap for using metadata for 
    all datasets below basedir'''

    os.makedirs(os.path.dirname(index_file), exist_ok=True)
    datasets = []
    with open(sitemap_file, 'w', encoding='utf-8') as fh:
        for (dataset_name, dpc_data) in dpcs(basedir+'/**/dpc.json'):
            dataset = _enhanced_linked_data(dpc_data['ld+json'], dataset_name, dpc_data.get('image'), dpc_host)
            datasets.append(dataset)
            fh.write('{}\n'.format(dataset['landingPage']))

    template = env.get_template('index_template.html')
    rendered_template = template.render(datasets = datasets)
    with open(index_file, 'w') as fh:
        fh.write(rendered_template)
 
# TODO include validation result ()
def render_landing_page(dpc_file, dst_file, ld_file, datapackage_file, dataset_name, validation_results_file, DPC_CONFIG):
    '''Render the dataset index page using metadata from supplied dpc file'''
    # Open template file
    template = env.get_template('dataset_template.html')

    dpc_data = _load_dpc_file(dpc_file)
    ld = dpc_data['ld+json']

    size = os.path.getsize(validation_results_file)
    validation_ok = True if os.path.getsize(validation_results_file) == 0 else False
    
    # render template with ld supplied as params
    rendered_template = template.render(ld = ld, image_url=dpc_data.get('image'), validation_ok = validation_ok, size = size)

    datapackage_template = env.get_template('datapackage.json')
    dataset = _enhanced_linked_data(ld, dataset_name, dpc_data.get('image'), DPC_CONFIG['host'])
    rendered_dp_template = datapackage_template.render(ld = dataset)

    # Write to dest file
    os.makedirs(os.path.dirname(dst_file), exist_ok=True)
    with open(dst_file, 'w') as fh:
        fh.write(rendered_template)
    with open(ld_file, 'w') as fh:
        json.dump(ld, fh)
    with open(datapackage_file, 'w') as fh:
        fh.write(rendered_dp_template)

def _as_error_dict(error):
    return {
                'line': error.line, 
                'column': error.column,
                'level': error.level_name,
                'message': error.message,
                'domain_name': error.domain_name,
                'type_name': error.type_name
            }

def validate_xml(xml_file, fallback_schema, dst_file):
    doc = etree.parse(xml_file)

    with jsonlines.open(dst_file, mode='w') as writer:
        schema = validate_XML(doc)
        for error in schema.error_log:
            writer.write(_as_error_dict(error))

        if fallback_schema and len(schema.error_log) == 1 and "No matching global declaration" in schema.error_log[0].message:
            xmlns = etree.QName(doc.getroot().tag).namespace
            schema = validate_XML(doc, [u"%s %s"%(xmlns, fallback_schema)])
            for error in schema.error_log:
                writer.write(_as_error_dict(error))

def validate_xml_via_schematron(xml_file, schema_file, dst_file):
    schematron = Schematron(file = schema_file,
        error_finder=Schematron.ASSERTS_AND_REPORTS)
    doc = etree.parse(xml_file)
    valid = schematron.validate(doc)

    ns = {'svrl': 'http://purl.oclc.org/dsdl/svrl'}

    with jsonlines.open(dst_file, mode='w') as writer:
        for error in schematron.error_log:
            msg_xml = etree.fromstring(error.message)
            message = msg_xml.find('svrl:text', ns).text if msg_xml.find('svrl:text', ns) is not None else None

            error_dict = {
                'line': error.line, 
                'column': error.column,
                'level': error.level_name,
                'message': message,
                'domain_name': error.domain_name,
                'type_name': error.type_name
            }
            writer.write(error_dict)
   
def merge_validation_results(validation_files, dst_file):
    with open(dst_file, 'w') as fh:
        for in_file in validation_files:
            # read row by row, collect only n samples of same category and count rest, write them out as result file
            with open(in_file, 'r') as rh:
                for line in rh:
                    # TODO here we should do some counting...
                    fh.write(line) 

def render_validation_results(results_file, dpc_file, dst_file):
    template = env.get_template('validation_results_template.html')

    ld = _load_linked_data(dpc_file)
    
    with open(results_file, 'r', encoding='utf-8') as rh:
        data = jsonlines.Reader(rh).iter(type=dict, skip_invalid=True)
        rendered_template = template.render(errors = data, ld = ld)

        with open(dst_file, 'w') as fh:
            fh.write(rendered_template) 


    