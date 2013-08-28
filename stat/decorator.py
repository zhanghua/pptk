import cProfile
from memory_profiler import LineProfiler
import linecache
import inspect
import time, io, sys, os

profile_data_dir = '/opt/stack/data/swift/profile/'

def cpu_profiler(func):
    def profiled_fn(*args, **kwargs):
        ts =  time.time()
        fpath = ''.join([profile_data_dir, func.__name__ , str(ts), ".cprofile"])
        prof = cProfile.Profile()
        pcall  = prof.runcall(func, *args, **kwargs)
        prof.dump_stats(fpath)
        return pcall
    return profiled_fn

def mem_profiler(func):
    def profiled_fn(*args, **kwargs):
        ts =  time.time()
        prof = LineProfiler()
        val = prof(func)(*args, **kwargs)
        fpath = ''.join([profile_data_dir, func.__name__ , str(ts), ".mprofile"])
        astream = io.open(fpath,'w')
        show_results(prof, astream, precision=3)
        astream.flush()
        return val
    return profiled_fn
    
def show_results(prof, stream=None, precision=3):
    if stream is None:
        stream = sys.stdout
    template = '{0:>6} {1:>12} {2:>12}   {3:<}'
    
    try:
        for code in prof.code_map:
            lines = prof.code_map[code]
            if not lines:
                # .. measurements are empty ..
                continue
            filename = code.co_filename
            if filename.endswith((".pyc", ".pyo")):
                filename = filename[:-1]
            stream.write(unicode('Filename: ' + filename + '\n\n'))
            if not os.path.exists(filename):
                stream.write(unicode('ERROR: Could not find file ' + filename + '\n'))
                if filename.startswith("ipython-input") or filename.startswith("<ipython-input"):
                    print("NOTE: %mprun can only be used on functions defined in "
                          "physical files, and not in the IPython environment.")
                continue
            all_lines = linecache.getlines(filename)
            sub_lines = inspect.getblock(all_lines[code.co_firstlineno - 1:])
            linenos = range(code.co_firstlineno, code.co_firstlineno +
                            len(sub_lines))
            lines_normalized = {}
    
            header = template.format('Line #', 'Mem usage', 'Increment',
                                     'Line Contents')
            stream.write(unicode(header + '\n'))
            stream.write(unicode('=' * len(header) + '\n'))
            # move everything one frame up
            keys = sorted(lines.keys())
    
            k_old = keys[0] - 1
            lines_normalized[keys[0] - 1] = lines[keys[0]]
            for i in range(1, len(lines_normalized[keys[0] - 1])):
                lines_normalized[keys[0] - 1][i] = -1.
            k = keys.pop(0)
            while keys:
                lines_normalized[k] = lines[keys[0]]
                for i in range(len(lines_normalized[k_old]),
                               len(lines_normalized[k])):
                    lines_normalized[k][i] = -1.
                k_old = k
                k = keys.pop(0)
    
            first_line = sorted(lines_normalized.keys())[0]
            mem_old = max(lines_normalized[first_line])
            precision = int(precision)
            template_mem = '{{0:{0}.{1}'.format(precision + 6, precision) + 'f} MB'
            for i, l in enumerate(linenos):
                mem = ''
                inc = ''
                if l in lines_normalized:
                    mem = max(lines_normalized[l])
                    inc = mem - mem_old
                    mem_old = mem
                    mem = template_mem.format(mem)
                    inc = template_mem.format(inc)
                stream.write(unicode(template.format(l, mem, inc, sub_lines[i])))
            stream.write(unicode('\n\n'))
    except Exception as e:
        print "Exception happens when profiling memory: ", e
