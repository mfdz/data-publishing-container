import glob
import dpc.tasks as tasks
from doit import create_after

DOIT_CONFIG = {
    'action_string_formatting': 'new',
    'check_file_uptodate': 'timestamp'
}

DPC_CONFIG = {
    'host': 'data.mfdz.de',
    'dataset_template': 'config/templates/dataset_template.html',
    'datapackage_template': 'config/templates/datapackage.json',
    'out_dir': 'out/',
    'dataset_definitions_dir': 'config/datasets/' 
}

def task_copy_static_files():
    '''copy static files to publish dir'''
    return {
            'actions': ['mkdir -p {0} && cp -rf config/static/* {0}'.format(DPC_CONFIG['out_dir'])],
        }

def task_render_index():
    '''render index.html and sitemap.txt for datasets'''
    SITEMAP = DPC_CONFIG['out_dir'] + 'sitemap.txt'
    INDEX = DPC_CONFIG['out_dir'] + 'index.html'
    
    return {
        'targets': [SITEMAP, INDEX],
        'actions': [(tasks.render_index, [DPC_CONFIG['dataset_definitions_dir'], DPC_CONFIG['host'], INDEX, SITEMAP])],
    }


def task_download_mdm_dataset():
    for (dataset_name, download_url, cert, file_type) in tasks.download_links(DPC_CONFIG['dataset_definitions_dir']+'**/dpc.json'):
        dst_file = DPC_CONFIG['out_dir'] + dataset_name + '/body.' + file_type

        action = 'curl -fsS -z {targets} -o {targets} --create-dirs -R --compressed '
        if cert:
            action = action + '--cert ' + cert
        yield {
            'name': dataset_name,
            'targets': [dst_file],
            'actions': [action + ' ' + download_url]
        }

def task_validate_xml():
    for (dataset_name, dpc_def) in tasks.dpcs(DPC_CONFIG['dataset_definitions_dir']+'**/dpc.json'):
        if dpc_def['fileType'] != 'xml':
            continue

        body_file = DPC_CONFIG['out_dir'] + dataset_name + '/body.xml'
        dst_file = DPC_CONFIG['out_dir'] + dataset_name + '/validation_results.schema.jsonl'
        fallback_schema = dpc_def["ld+json"].get('schema') 
        
        yield {
            'name': dataset_name,
            'file_dep': [body_file],
            'targets': [dst_file],
            'actions': [(tasks.validate_xml, (body_file, fallback_schema, dst_file, '.schema_cache'))]
        }    

def task_validate_xml_using_schematron():
    for (dataset_name, schematron_file) in tasks.datasets_with_schematron_validation(DPC_CONFIG['dataset_definitions_dir']+'**/dpc.json'):
       
        body_file = DPC_CONFIG['out_dir'] + dataset_name + '/body.xml'
        dst_file = DPC_CONFIG['out_dir'] + dataset_name + '/validation_results.schematron.jsonl'
        
        yield {
            'name': dataset_name,
            'file_dep': [body_file, schematron_file],
            'targets': [dst_file],
            'actions': [(tasks.validate_xml_via_schematron, (body_file, schematron_file, dst_file))]
        }

@create_after(executed='validate_xml', target_regex='.*/validation_results.jsonl')
@create_after(executed='validate_xml_using_schematron', target_regex='.*/validation_results.jsonl')
def task_merge_validation_results():
    for (dataset_name, validation_files) in tasks.datasets_out_files(DPC_CONFIG['dataset_definitions_dir']+'**/dpc.json', DPC_CONFIG['out_dir'], 'validation_results.*.jsonl'):
        dst_file = DPC_CONFIG['out_dir'] + dataset_name + '/validation_results.jsonl'
        yield {
            'name': dataset_name,
            'file_dep': validation_files,
            'targets': [dst_file],
            'actions': [(tasks.merge_validation_results, (validation_files, dst_file))]
        }

def task_render_validation_results():
    for (dataset_name, dpc_file) in tasks.dpc_files(DPC_CONFIG['dataset_definitions_dir']+'**/dpc.json'):
        validation_results_file = DPC_CONFIG['out_dir'] + dataset_name + '/validation_results.jsonl'
        dst_file = DPC_CONFIG['out_dir'] + dataset_name + '/validation_results.html'
    
        yield {
            'name': dataset_name,
            'file_dep': [validation_results_file],
            'targets': [dst_file],
            'actions': [(tasks.render_validation_results, (validation_results_file, dpc_file, dst_file))]
        }

def task_render_landing_page():
    '''render index.html page for datasets'''
    for (dataset_name, dpc_file) in tasks.dpc_files(DPC_CONFIG['dataset_definitions_dir']+'**/dpc.json'):
        dst_file = DPC_CONFIG['out_dir'] + dataset_name + '/index.html'
        ld_file = DPC_CONFIG['out_dir'] + dataset_name + '/ld.json'
        validation_results_file = DPC_CONFIG['out_dir'] + dataset_name + '/validation_results.jsonl'
        
        datapackage_file = DPC_CONFIG['out_dir'] + dataset_name + '/datapackage.json'
        
        yield {
            'name': dataset_name,
            'file_dep': [dpc_file, validation_results_file, DPC_CONFIG['dataset_template'], DPC_CONFIG['datapackage_template']],
            'targets': [dst_file, ld_file, datapackage_file],
            'actions': [(tasks.render_landing_page, [dpc_file, dst_file, ld_file, datapackage_file, dataset_name, validation_results_file, DPC_CONFIG])],
        }
    