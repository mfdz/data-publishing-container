import glob
import json
import os
from lxml import etree
from jinja2 import Environment, FileSystemLoader, select_autoescape
from .schemavalidator import validate_XML
from lxml.isoschematron import Schematron

env = Environment(
    loader=FileSystemLoader('config/templates'),
    autoescape=select_autoescape([ 'xml'])
)

def dpc_files(pattern):
    LIST = glob.glob(pattern, recursive = True)
    for dpc_file in LIST:
        dataset_name = os.path.basename(os.path.dirname(dpc_file))
        yield (dataset_name, dpc_file)

def _load_linked_data(dpc_file):
    with open(dpc_file, encoding='utf-8') as fc:
        data = json.load(fc) 
        # extract ld section
        return data['ld+json']

def _replace_env_vars(value):
    if value and value.startswith('$DPC_'):
        return os.environ.get(value[1:])

def download_links(pattern):
    for (dataset_name, dpc_file) in dpc_files(pattern):
        # open dpc file
        with open(dpc_file, encoding='utf-8') as fc:
            data = json.load(fc)
            yield (dataset_name, data['downloadUrl'], data.get('downloadCert'), data['fileType'])

def datasets_with_schematron_validation(pattern):
    for (dataset_name, dpc_file) in dpc_files(pattern):
        # open dpc file
        with open(dpc_file, encoding='utf-8') as fc:
            data = json.load(fc)
            if data.get('fileType')=='xml' and data.get('schematron'):
                yield (dataset_name, data['schematron'])

def _format_for(encodingFormat):
    # FIXME this is temporary and should be replaced, e.g. by using datapackage's format metainfo
    if encodingFormat == "text/csv":
        return "csv"
    elif encodingFormat == "text/xml":
        return "xml"
    elif encodingFormat == "application/json":
        return "json"
    return"unknown"     


def _enhanced_linked_data(ld, dataset_name, dpc_host):
    dataset = ld.copy()
    dataset['image'] = f'https://{dpc_host}/img/data.jpg'
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
        for (dataset_name, dpc_file) in dpc_files(basedir+'/**/dpc.json'):
            ld = _load_linked_data(dpc_file)
            dataset = _enhanced_linked_data(ld, dataset_name, dpc_host)
            datasets.append(dataset)
            fh.write('{}\n'.format(dataset['landingPage']))

    template = env.get_template('index_template.html')
    rendered_template = template.render(datasets = datasets)
    with open(index_file, 'w') as fh:
        fh.write(rendered_template)
 
# TODO include validation result ()
def render_index_page(dpc_file, dst_file, ld_file, datapackage_file, dataset_name, DPC_CONFIG):
    '''Render the dataset index page using metadata from supplied dpc file'''
    # Open template file
    template = env.get_template('dataset_template.html')
    ld = _load_linked_data(dpc_file)
    
    # render template with ld supplied as params
    rendered_template = template.render(ld = ld)

    datapackage_template = env.get_template('datapackage.json')
    dataset = _enhanced_linked_data(ld, dataset_name, DPC_CONFIG['host'])
    rendered_dp_template = datapackage_template.render(ld = dataset)

    # Write to dest file
    os.makedirs(os.path.dirname(dst_file), exist_ok=True)
    with open(dst_file, 'w') as fh:
        fh.write(rendered_template)
    with open(ld_file, 'w') as fh:
        json.dump(ld, fh)
    with open(datapackage_file, 'w') as fh:
        fh.write(rendered_dp_template)


def validate_xml(xml_file, dst_file):
    doc = etree.parse(xml_file)
    schema = validate_XML(doc)
    with open(dst_file, 'w') as fh:
        for error in schema.error_log:
            fh.write(f'{error}\n')

def validate_xml_via_schematron(xml_file, schema_file, dst_file):
    schematron = Schematron(file = schema_file,
        error_finder=Schematron.ASSERTS_AND_REPORTS)
    doc = etree.parse(xml_file)
    valid = schematron.validate(doc)

    ns = {'svrl': 'http://purl.oclc.org/dsdl/svrl'}

    with open(dst_file, 'w') as fh:
        for error in schematron.error_log:
            msg_xml = etree.fromstring(error.message)
            message = msg_xml.find('svrl:text', ns).text if msg_xml.find('svrl:text', ns) is not None else None
            fh.write(u'%s:%d:%d:%s:%s:%s: %s\n' % (
                error.filename, error.line, error.column, error.level_name,
                error.domain_name, error.type_name, message))
            

    