import os
import logging

import taskgraph
import pygeoprocessing
import pandas
import numpy

from .. import utils

LOGGER = logging.getLogger(__name__)


def execute(args):
    suffix = utils.make_suffix_string(args, 'results_suffix')
    output_dir = os.path.join(args['workspace_dir'], 'outputs')
    intermediate_dir = os.path.join(args['workspace_dir'], 'intermediate')
    taskgraph_cache_dir = os.path.join(intermediate_dir, 'task_cache')

    utils.make_directories([output_dir, intermediate_dir, taskgraph_cache_dir])

    try:
        n_workers = int(args['n_workers'])
    except (KeyError, ValueError, TypeError):
        # KeyError when n_workers is not present in args
        # ValueError when n_workers is an empty string.
        # TypeError when n_workers is None.
        n_workers = -1  # Synchronous mode.
    task_graph = taskgraph.TaskGraph(
        taskgraph_cache_dir, n_workers, reporting_interval=5.0)

    if 'transitions_csv' in args and args['transitions_csv'] not in ('', None):
        transitions = _extract_transitions_from_table(args['transitions_csv'])
    else:
        transitions = {}

    baseline_lulc_info = pygeoprocessing.get_raster_info(
        args['baseline_lulc_path'])
    target_sr_wkt = baseline_lulc_info['projection_wkt']
    min_pixel_size = numpy.min(numpy.abs(baseline_lulc_info['pixel_size']))
    target_pixel_size = (min_pixel_size, -min_pixel_size)

    transition_years = set()
    try:
        transition_years.add(int(args['baseline_lulc_year']))
    except (KeyError, ValueError, TypeError):
        LOGGER.error('The baseline_lulc_year is required but not provided.')
        raise ValueError('Baseline lulc year is required.')

    try:
        transition_years.add(int(args['analysis_year']))
    except (KeyError, ValueError, TypeError):
        pass

    base_paths = [args['baseline_lulc_path']]
    aligned_paths = [os.path.join(
        intermediate_dir, f'aligned_baseline_lulc{suffix}'.tif)]
    for transition_year in transitions:
        base_paths.append(transitions[transition_year])
        transition_years.add(transition_year)
        aligned_paths.append(
            os.path.join(
                intermediate_dir,
                f'aligned_transition_{transition_year}{suffix}.tif'))

    alignment_task = task_graph.add_task(
        func=pygeoprocessing.align_and_resize_raster_stack,
        args=(base_paths, aligned_paths, ['nearest']*len(base_paths),
              target_pixel_size, 'intersection'),
        kwargs={
            'target_projection_wkt': target_sr_wkt,
            'raster_align_index': 0,
        },
        hash_algorithm='md5',
        copy_duplicate_artifact=True,
        target_path_list=aligned_paths,
        task_name='Align input landcover rasters.')












def _extract_transitions_from_table(csv_path):
    encoding = None
    if utils.has_utf8_bom(csv_path):
        encoding = 'utf-8-sig'

    table = pandas.read_csv(
        csv_path, sep=None, index_col=False, engine='python',
        encoding=encoding)
    table.columns = table.columns.str.lower().strip()

    output_dict = {}
    table.set_index('transition_year', drop=False, inplace=True)
    for index, row in table.iterrows():
        output_dict[int(index)] = row['raster_path']

    return output_dict
