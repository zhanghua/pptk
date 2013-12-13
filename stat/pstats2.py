"""Class for printing reports on profiled python code."""

# Written by James Roskind
# Based on prior profile module by Sjoerd Mullender...
#   which was hacked somewhat by: Guido van Rossum

# Copyright Disney Enterprises, Inc.  All Rights Reserved.
# Licensed to PSF under a Contributor Agreement
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied.  See the License for the specific language
# governing permissions and limitations under the License.


import sys
import os
import time
import marshal
import re
import subprocess
import json
import glob
import tempfile
from functools import cmp_to_key
from dictformat import format_dict
from pstats import Stats
try:
    import matplotlib.pyplot as plt
except:
    pass
import numpy as np

__all__ = ["Stats"]


#**************************************************************************
# func_name is a triple (file:string, line:int, name:string)

def func_strip_path(func_name):
    filename, line, name = func_name
    return os.path.basename(filename), line, name

def func_get_function_name(func):
    return func[2]

def func_std_string(func_name): # match what old profile produced
    if func_name[:2] == ('~', 0):
        # special case for built-in functions
        name = func_name[2]
        if name.startswith('<') and name.endswith('>'):
            return '{%s}' % name[1:-1]
        else:
            return name
    else:
        return "%s:%d(%s)" % func_name

def func_to_dict(func):
    return {'module': func[0], 'line': str(func[1]), 'function': func[2]}

#**************************************************************************
# The following functions combine statists for pairs functions.
# The bulk of the processing involves correctly handling "call" lists,
# such as callers and callees.
#**************************************************************************

def add_func_stats(target, source):
    """Add together all the stats for two profile entries."""
    cc, nc, tt, ct, callers = source
    t_cc, t_nc, t_tt, t_ct, t_callers = target
    return (cc+t_cc, nc+t_nc, tt+t_tt, ct+t_ct,
              add_callers(t_callers, callers))

def add_callers(target, source):
    """Combine two caller lists in a single list."""
    new_callers = {}
    for func, caller in target.iteritems():
        new_callers[func] = caller
    for func, caller in source.iteritems():
        if func in new_callers:
            if isinstance(caller, tuple):
                # format used by cProfile
                new_callers[func] = tuple([i[0] + i[1] for i in
                                           zip(caller, new_callers[func])])
            else:
                # format used by profile
                new_callers[func] += caller
        else:
            new_callers[func] = caller
    return new_callers

def count_calls(callers):
    """Sum the caller statistics to get total number of calls received."""
    nc = 0
    for calls in callers.itervalues():
        nc += calls
    return nc

#**************************************************************************
# The following functions support printing of reports
#**************************************************************************

def f8(x):
    return "%8.3f" % x

#**************************************************************************
# Statistics browser added by ESR, April 2001
#**************************************************************************

def to_json(stats, file):
    d = dict()
    d['files'] = [ f for f in stats.files ]
    d['prim_calls'] = str(stats.prim_calls)
    d['total_calls'] = str(stats.total_calls)
    if hasattr(self, 'sort_type'):
        d['sort_type'] = stats.sort_type
    d['total_tt'] = str(stats.total_tt)
    function_calls = []
    for func, (cc, nc, tt, ct, callers) in stats.stats.items():
        fdict = dict()
        fdict.update(func_to_dict(func))
        fdict.update({'cc': str(cc), 'nc': str(nc), 'tt': str(tt), 'ct': str(ct)})
        c = []
        for caller in callers:
            c.append(func_to_dict(caller))
        fdict.update({'callers': c })
        function_calls.append(fdict)
    d['stats'] = function_calls
    print json.dumps(d, indent=2)
    #file = open(file, mode='w')
    #json.dump(d, fp=file, check_circular=True, indent='  ')    
        
if __name__ == '__main__':
    import cmd
    try:
        import readline
    except ImportError:
        pass

    class ProfileBrowser(cmd.Cmd):
        def __init__(self, profile=None):
            cmd.Cmd.__init__(self)
            self.prompt = "% "
            self.stats = None
            self.stream = sys.stdout
            if profile is not None:
                self.do_read(profile)

        def generic(self, fn, line):
            args = line.split()
            processed = []
            for term in args:
                try:
                    processed.append(int(term))
                    continue
                except ValueError:
                    pass
                try:
                    frac = float(term)
                    if frac > 1 or frac < 0:
                        print >> self.stream, "Fraction argument must be in [0, 1]"
                        continue
                    processed.append(frac)
                    continue
                except ValueError:
                    pass
                processed.append(term)
            if self.stats:
                getattr(self.stats, fn)(*processed)
            else:
                print >> self.stream, "No statistics object is loaded."
            return 0

        def generic_help(self):
            print >> self.stream, "Arguments may be:"
            print >> self.stream, "* An integer maximum number of entries to print."
            print >> self.stream, "* A decimal fractional number between 0 and 1, controlling"
            print >> self.stream, "  what fraction of selected entries to print."
            print >> self.stream, "* A regular expression; only entries with function names"
            print >> self.stream, "  that match it are printed."

        def do_add(self, line):
            print "adding profile", line
            if not self.stats:
                print >> self.stream, "No statistics object is loaded."
                return 0
            if "*" in line or "?" in line:
                    pathes = glob.glob(line)
                    print >> self.stream, "files: ", pathes
                    for p in pathes:
                        self.do_add(p)
                    return
            if not os.path.isfile(line):
                print >> self.stream, "The file %s doesn't exist." % line
                return 0
            if self.is_loaded("    " + line):
                print >> self.stream, "This profile '%s' has already been loaded." % line
                return 0
            self.stats.add(line)
            return 0
        def help_add(self):
            print >> self.stream, "Add profile info from given file to current statistics object."
        def is_loaded(self, fn):
            for f in self.stats.files:
                if f.endswith(fn):
                    return True
            return False

        def do_callees(self, line):
            return self.generic('print_callees', line)
        def help_callees(self):
            print >> self.stream, "Print callees statistics from the current stat object."
            self.generic_help()

        def do_callers(self, line):
            return self.generic('print_callers', line)
        def help_callers(self):
            print >> self.stream, "Print callers statistics from the current stat object."
            self.generic_help()

        def do_EOF(self, line):
            print >> self.stream, ""
            return 1
        def help_EOF(self):
            print >> self.stream, "Leave the profile brower."

        def do_quit(self, line):
            return 1
        def help_quit(self):
            print >> self.stream, "Leave the profile brower."

        def do_read(self, line):
            if "*" in line or "?" in line:
                pathes = glob.glob(line)
                print >> self.stream, "This is an unix path pattern which match files: "
                print >> self.stream, pathes
                if pathes and len(pathes)>1:
                    self.stats = Stats(pathes[0])
                    for p in pathes[1:]:
                        self.do_add(p)
                    return
            if line:
                try:
                    self.stats = Stats(line)
                except IOError, args:
                    print >> self.stream, args[1]
                    return
                except Exception as err:
                    print >> self.stream, err.__class__.__name__ + ':', err
                    return
                self.prompt = line + "% "
            elif len(self.prompt) > 2:
                line = self.prompt[:-2]
                self.do_read(line)
            else:
                print >> self.stream, "No statistics object is current -- cannot reload."
            return 0
        def help_read(self):
            print >> self.stream, "Read in profile data from a specified file."
            print >> self.stream, "Without argument, reload the current file."

        def do_reverse(self, line):
            if self.stats:
                self.stats.reverse_order()
            else:
                print >> self.stream, "No statistics object is loaded."
            return 0
        def help_reverse(self):
            print >> self.stream, "Reverse the sort order of the profiling report."

        def do_sort(self, line):
            if not self.stats:
                print >> self.stream, "No statistics object is loaded."
                return
            abbrevs = self.stats.get_sort_arg_defs()
            if line and all((x in abbrevs) for x in line.split()):
                self.stats.sort_stats(*line.split())
            else:
                print >> self.stream, "Valid sort keys (unique prefixes are accepted):"
                for (key, value) in Stats.sort_arg_dict_default.iteritems():
                    print >> self.stream, "%s -- %s" % (key, value[1])
            return 0
        def help_sort(self):
            print >> self.stream, "Sort profile data according to specified keys."
            print >> self.stream, "(Typing `sort' without arguments lists valid keys.)"
        def complete_sort(self, text, *args):
            return [a for a in Stats.sort_arg_dict_default if a.startswith(text)]

        def do_stats(self, line):
            return self.generic('print_stats', line)
        def help_stats(self):
            print >> self.stream, "Print statistics from the current stat object."
            self.generic_help()

        def do_strip(self, line):
            if self.stats:
                self.stats.strip_dirs()
            else:
                print >> self.stream, "No statistics object is loaded."
        def help_strip(self):
            print >> self.stream, "Strip leading path information from filenames in the report."

        def help_help(self):
            print >> self.stream, "Show help for a given command."

        def postcmd(self, stop, line):
            if stop:
                return stop
            return None 
        
        def do_dump(self, line):
            if line:
                args = line.split()
                try:
                    self.stats.dump_stats(args[0])
                except Exception as e:
                    print >> self.stream, e
            else:
                print >> self.stream, "Need to provide a file name to dump."
                
        def help_dump(self):
            print >> self.stream, "Dump current profile data into a given file."
        
        def do_tojson(self, line):
            if not self.stats:
                print >> self.stream, "Need to load profile at first."
                return            
            if line:
                args = line.split()
                try:
                    to_json(self.stats, args[0])
                except Exception as e:
                    print >> self.stream, e
            else:
                print >> self.stream, "Need to provide a file name to export."
        
        def help_tojson(self):
            print >> self.stream, "Export stats output to a file with specified format of JSON or CSV."
        
        def do_rawdata(self, line):
            if not self.stats:
                print >> self.stream, "Need to load profile at first."
                return
            print >> self.stream, format_dict(self.stats.__dict__, tab=2)
        
        def help_rawdata(self):
            print >> self.stream, "Dump the raw dictionary data."
            
        def do_list(self, line):
            if self.stats and self.stats.files:
                for filename in self.stats.files:
                    print >> self.stream, filename
            else:
                print >> self.stream, "No profile loaded."
        def help_list(self):
            print >> self.stream, "List all profile files. "

        def do_runsnake(self, line):
            if not self.stats:
                print >> self.stream, "Need to load profile at first."
                return            
            ts = time.time()
            tmp_profile = '/tmp/runsnake.profile.' + str(ts)
            self.stats.dump_stats(tmp_profile)
            try:
                subprocess.call(['runsnake', tmp_profile])
            except:
                print >> self.stream, "Can not launch runsnake. please verify it has been installed."
            os.remove(tmp_profile)
            
        def help_runsnake(self):
            print >> self.stream, "Draw square box by runsnake."
            
        def do_kcachegrind(self, line):
            if not self.stats:
                print >> self.stream, "Need to load profile at first."
                return
            import pyprof2calltree
            conv = pyprof2calltree.CalltreeConverter(self.stats)
            grind = None
            ts = time.time()
            tmp_cachegrind_file = tempfile.mkstemp('.profile', 'cachegrind-')
            print >> self.stream, tmp_cachegrind_file
            try:
                #grind = open(tmp_cachegrind_file, 'wb')
                conv.output(tmp_cachegrind_file)
                subprocess.call(['kcachegrind', tmp_cachegrind_file])
                os.remove(tmp_cachegrind_file)
            except TypeError:
                print >> self.stream, "Can not convert into grind format."
            except OSError:
                print >> self.stream, "Can not launch kcachegrind. please verify it has been installed."
            except Exception as ex:
                print >> self.stream, "Error:", type(ex)
            finally:
                if grind is not None:
                    grind.close()

        
        def help_kcachegrind(self):
            print >> self.stream, "Draw call tree by kcachegrind."
            
        def do_plot(self, line):
            args = line.split()
            if not self.stats or not line or len(args)<3:
                print >> self.stream, "Need to load profile at first. "
                print >> self.stream, "Usage: plot bar cc|nc|tt|ct [query] limit"
                print >> self.stream, "       plot pie cc|nc|tt|ct [query] limit"
                return
            limit = 10
            query = ''
            
            
            [type, counter, query, limit]  = ['bar', 'cc', '', int(args[2])] if len(args) == 3  \
                               else [args[0], args[1],args[2], int(args[3])]
            print query, limit
            nfls = []
            performance=[]
            stats_dict = self.stats.stats
            width, list = self.stats.get_print_list([query])
            for func in list:
                cc, nc, tt, ct, callers = stats_dict[func]
                matrix = {'cc': cc, 'nc': nc, 'tt': tt, 'ct':ct }
                names = {'cc': 'Call Count', 'nc': 'NC', 'tt': 'Total Time', 'ct':'Cumulative Time' }
                if limit<1:
                    break
                nfls.append(func[2])
                performance.append(matrix[counter])
                limit-=1
            print "Functions: %s" % nfls
            print "Performance: %s" % performance
            y_pos = np.arange(len(nfls))
            error = np.random.rand(len(nfls))
            axes = plt.gca()
            if type == 'bar':
                plt.barh(y_pos, performance, xerr=error, align='center', alpha=0.4)
                plt.yticks(y_pos, nfls)
                plt.xlabel(names[counter])
            elif type == 'pie':
                plt.pie(x=performance, explode=None, labels=nfls, shadow=True)
            plt.title('Profile Statistics (by %s)' % counter)

            plt.show()
        
        def help_plot(self):
            print >> self.stream, "Draw plot based on current data."
        
    import sys
    if len(sys.argv) > 1:
        initprofile = sys.argv[1]
    else:
        initprofile = None
    try:
        browser = ProfileBrowser(initprofile)
        print >> browser.stream, "Welcome to the profile statistics browser."
        browser.cmdloop()
        print >> browser.stream, "Goodbye."
    except KeyboardInterrupt:
        pass

# That's all, folks.
