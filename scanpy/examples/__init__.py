# Author: F. Alex Wolf (http://falexwolf.de)
"""
Example Data and Example Use Cases
"""

from __future__ import print_function
import os
from . import builtin
from .. import utils
from .. import readwrite
from .. import settings as sett

def get_example(exkey, subsample=1, return_module=False):
    """
    Read and preprocess data for predefined example.

    Parameters
    ----------
    exkey : str
        Key for the example dictionary in _examples.
    subsample : int
        Subsample to a fraction of 1/subsample of the data.
    return_module : bool, optional
        Return example module.

    Returns
    -------
    adata : AnnData
        Annotated data matrix, optionally with metadata such as
        adata['xroot'] : np.ndarray or int
            Expression vector or index of root cell for DPT analysis.

    Returns additionally, if return_module == True:
    exmodule : dict, optional
        Example module.
    """
    loop_over_filenames = [filename for filename in os.listdir('.')
                           if filename.startswith('scanpy') and filename.endswith('.py')]
    if len(loop_over_filenames) == 0:
        sett.m(0, '--> did not find user examples, to provide some,\n'
               '    generate a file scanpy_whatevername.py in your working directory,\n'
               '    see https://github.com/theislab/scanpy#work-on-your-own-examples')
    not_found = True
    from sys import path
    path.insert(0, '.')
    for filename in loop_over_filenames:
        exmodule = __import__(filename.replace('.py',''))
        try:
            exfunc = getattr(exmodule, exkey)
            not_found = False
        except AttributeError:
            pass
    if not_found:
        try:
            # additional possibility to add example module
            from . import builtin_private
            exfunc = getattr(builtin_private, exkey)
            exmodule = builtin_private
        except (ImportError, AttributeError):
            try:
                exfunc = getattr(builtin, exkey)
                exmodule = builtin
            except AttributeError:
                msg = ('Do not know how to run example "' + exkey +
                       '".\nEither define a function ' + exkey + '() '
                       'in ./scanpy_user.py that returns an AnnData object.\n'
                       'Or, use one of the builtin examples:'
                       + _exkeys_str())
                from sys import exit
                exit(msg)

    from os.path import exists
    exfile = readwrite.get_filename_from_key(sett.basekey)
    if (not exists(exfile)
        or sett.recompute in ['read', 'pp']):
        # run the function
        adata = exfunc()
        # add exkey to adata
        # adata['exkey'] = exkey
        sett.m(0, 'X has shape n_samples x n_variables =', 
               adata.X.shape[0], 'x', adata.X.shape[1])
        # do sanity checks on data dictionary
        adata = check_adata(adata, verbosity=1)

        # subsampling
        if subsample != 1:
            from ..preprocess import subsample as subsample_function
            adata = subsample_function(adata, subsample)

        readwrite.write(sett.basekey, adata)
        sett.m(0, 'wrote preprocessed data to', exfile)
    else:
        adata = readwrite.read(sett.basekey)

    if return_module:
        return adata, exmodule
    else:
        return adata

def show_exdata(format='plain'):
    """Show available example data.
    """
    if format == 'plain':
        s = utils.pretty_dict_string(builtin.example_data)
    elif format == 'markdown':
        s = utils.markdown_dict_string(builtin.example_data)
    print(s)

def show_exparams():
    """Show available example use cases.
    """
    s = utils.pretty_dict_string(_example_parameters())
    print(s)

def _example_parameters():
    """Example use cases.
    """
    builtin_dex = utils.fill_in_datakeys(builtin.example_parameters, builtin.example_data)
    all_dex = utils.merge_dicts(builtin_dex, {}) 
    try:
        # additional possibility to add example module
        from . import builtin_private
        builtin_private_dex = utils.fill_in_datakeys(builtin_private.example_parameters, 
                                                  builtin_private.example_data)
        all_dex = utils.merge_dicts(all_dex, builtin_private_dex) 
    except ImportError:
        pass
    return all_dex

#-------------------------------------------------------------------------------
# Checks of AnnData object
#-------------------------------------------------------------------------------

_ignore_groups = ['N/A', 'dontknow', 'no_gate']
# howtos
_howto_specify_subgroups = '''sample annotation in adata only consists of sample names
--> you can provide additional annotation by setting, for example,
    adata.smp['groups'] = ['A', 'B', 'A', ... ]
    adata.smp['time'] = [0.1, 0.2, 0.7, ... ]'''

def check_adata(adata, verbosity=0):
    """
    Do sanity checks on adata object.

    Checks whether adata contains annotation.
    """
    import numpy as np
    import sys
    if 'tools' not in adata:
        adata['tools'] = np.array([], dtype=str)
    if len(adata.smp_keys()) == 0:
        sett.m(1-verbosity, _howto_specify_subgroups)
    else:
        if len(adata.smp_keys()) > 0 and sett.verbosity > 1-verbosity:
            info = 'continuous/categorical sample annotation with '
        for ismp, smp in enumerate(adata.smp_keys()):
            # ordered unique categories for categorical annotation
            if not smp + '_names' in adata and adata.smp[smp].dtype.char == 'U':
                adata[smp + '_names'] = np.unique(adata.smp[smp])
                if adata[smp + '_names'].dtype.char == 'U':
                    adata[smp + '_names'] = np.setdiff1d(adata[smp + '_names'],
                                                       np.array(_ignore_groups))
                try:
                    from natsort import natsorted
                    adata[smp + '_names'] = np.array(natsorted(adata[smp + '_names'], 
                                                               key=lambda v: v.upper()))
                except:
                    adata[smp + '_names'] = np.array(sorted(adata[smp + '_names'], 
                                                            key=lambda v: v.upper()))
                    pass
            if sett.verbosity > 1-verbosity:
                info += smp + ': '
                if adata.smp[smp].dtype.char == 'U':
                    ann_info = str(adata[smp + '_names'])
                    if len(adata[smp + '_names']) > 7:
                        ann_info = (str(adata[smp + '_names'][0:3]).replace(']','') 
                                    + ' ...' 
                                    + str(adata[smp + '_names'][-2:]).replace('[',''))
                    info += ann_info
                else:
                    info += 'cont'
                if ismp < len(adata.smp_keys())-1:
                    info += ','
                sett.m(1-verbosity, info)
        sett.m(1-verbosity, '')
    return adata

def _exkeys_str():
    str = ''
    for k in sorted(_example_parameters().keys()):
        str += '\n    ' + k
    return str
