import glob
from dpc.tasks import render_index_page, download_links, dpc_files, validate_xml, validate_xml_via_schematron, render_index, datasets_with_schematron_validation

DOIT_CONFIG = {
    'action_string_formatting': 'new'
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

def task_render_landing_page():
    '''render index.html page for datasets'''
    for (dataset_name, dpc_file) in dpc_files(DPC_CONFIG['dataset_definitions_dir']+'**/dpc.json'):
        dst_file = DPC_CONFIG['out_dir'] + dataset_name + '/index.html'
        ld_file = DPC_CONFIG['out_dir'] + dataset_name + '/ld.json'
        datapackage_file = DPC_CONFIG['out_dir'] + dataset_name + '/datapackage.json'
        
        yield {
            'name': dataset_name,
            'file_dep': [dpc_file, DPC_CONFIG['dataset_template'], DPC_CONFIG['datapackage_template']],
            'targets': [dst_file, ld_file, datapackage_file],
            'actions': [(render_index_page, [dpc_file, dst_file, ld_file, datapackage_file, dataset_name, DPC_CONFIG])],
        }

def task_render_index():
    '''render index.html and sitemap.txt for datasets'''
    SITEMAP = DPC_CONFIG['out_dir'] + 'sitemap.txt'
    INDEX = DPC_CONFIG['out_dir'] + 'index.html'
    
    return {
        'targets': [SITEMAP, INDEX],
        'actions': [(render_index, [DPC_CONFIG['dataset_definitions_dir'], DPC_CONFIG['host'], INDEX, SITEMAP])],
    }


def task_download_mdm_dataset():
    for (dataset_name, download_url, cert, file_type) in download_links(DPC_CONFIG['dataset_definitions_dir']+'**/dpc.json'):
        dst_file = DPC_CONFIG['out_dir'] + dataset_name + '/body.' + file_type

        action = 'curl  -z {targets} -o {targets} --create-dirs -R --compressed '
        if cert:
            action = action + '--cert ' + cert
        yield {
            'name': dataset_name,
            'targets': [dst_file],
            'actions': [action + ' ' + download_url]
        }

def task_validate_xml():
    for (dataset_name, download_url, cert, file_type) in download_links(DPC_CONFIG['dataset_definitions_dir']+'**/dpc.json'):
        if file_type != 'xml':
            continue

        body_file = DPC_CONFIG['out_dir'] + dataset_name + '/body.xml'
        dst_file = DPC_CONFIG['out_dir'] + dataset_name + '/validation_results.txt'
        
        yield {
            'name': dataset_name,
            'file_dep': [body_file],
            'targets': [dst_file],
            'actions': [(validate_xml, (body_file, dst_file))]
        }    

def task_validate_xml_using_schematron():
    for (dataset_name, schematron_file) in datasets_with_schematron_validation(DPC_CONFIG['dataset_definitions_dir']+'**/dpc.json'):
       
        body_file = DPC_CONFIG['out_dir'] + dataset_name + '/body.xml'
        dst_file = DPC_CONFIG['out_dir'] + dataset_name + '/validation_results_schematron.txt'
        
        yield {
            'name': dataset_name,
            'file_dep': [body_file, schematron_file],
            'targets': [dst_file],
            'actions': [(validate_xml_via_schematron, (body_file, schematron_file, dst_file))]
        }
