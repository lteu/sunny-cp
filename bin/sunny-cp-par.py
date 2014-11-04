# stable: 15/10 -- 20.21
# controllare con pattern set mining k1 - german credit

from threading import Thread
from multiprocessing import *
from subprocess import Popen, PIPE
from shutil import move
from math import isnan
from string import replace
import os
import fcntl
import signal
import sys
import time


# dictionary containing all the info about processes
processes = {}
# keys of processes
PROC_CMD = 0
PROC_TIMEOUT = 1
PROC_TIMEWAIT = 2
PROC_TIMEOBJ = 3
PROC_OUT = 4
PROC_SOL = 5
PROC_OBJ = 6
PROC_START = 7
PROC_TIMESOL = 8
PROC_PROC = 9
PROC_RESTART_OBJ = 10

SLEEP_TIME = 0.1

#def kill_process(proc):
  #if proc.poll() is None:
    ##proc.stdout.close()
    #pid = proc.pid
    ##os.killpg(pid, signal.SIGTERM)
    #os.killpg(pid, signal.SIGKILL)
    #print "% Killed process", pid, "and all its children"

import psutil
def kill_process(proc):
  if proc.poll() is None:
    pid = proc.pid
    process = psutil.Process(pid)
    for proc in process.get_children(recursive=True):
        proc.kill()
    process.kill()
    print "% Killed process", pid, "and all its children"
    


def handler(signum = None, frame = None):
  """
  Handles termination signals.
  """
  print >> sys.stderr, '% Signal handler called with signal',signum
  for i in processes:
    kill_process(processes[i][PROC_PROC])
  print >> sys.stderr, '% Killed all processes, exiting'
  os._exit(signum)
  
for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT]:
  signal.signal(sig, handler)


def inject(obj):
  """
  Inject the value.
  """
  with open('2DPacking.fzn') as infile:
    with open('tmp.fzn', 'w') as outfile:
      add = True
      for line in infile:
	if add and 'constraint' in line.split():
	  outfile.write('constraint int_lt(INT____00041, ' + str(obj) + ');\n')
	  add = False
	outfile.write(line)
  move('tmp.fzn', '2DPacking.fzn')

# class that makes a stream unbuffered  
class Unbuffered(object):
   def __init__(self, stream):
       self.stream = stream
   def write(self, data):
       self.stream.write(data)
       self.stream.flush()
   def __getattr__(self, attr):
       return getattr(self.stream, attr)

def launch_solver(i,cmd, timeout, timewait, timeobj, startobj):
  """
  Launches a solver.
  """
  
  if startobj != None:
    print '% Injecting value', startobj
    inject(startobj)
    
  processes[i] = {}
  processes[i][PROC_CMD] = cmd
  processes[i][PROC_TIMEOUT] = timeout
  processes[i][PROC_TIMEWAIT] = timewait
  processes[i][PROC_TIMEOBJ] = timeobj
  processes[i][PROC_OUT] = ""
  processes[i][PROC_SOL] = None
  processes[i][PROC_OBJ] = None
  processes[i][PROC_START] = time.time()
  processes[i][PROC_TIMESOL] = processes[i][PROC_START]

  processes[i][PROC_PROC] = Popen(cmd.split(), stdout = PIPE)
  # Non blocking read.
  fd = processes[i][PROC_PROC].stdout.fileno()
  fl = fcntl.fcntl(fd, fcntl.F_GETFL)
  fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
  
  processes[i][PROC_RESTART_OBJ] = startobj
  
  print "% Process", i, "(pid", processes[i][PROC_PROC].pid, ")"
	    

def read_lines(i):
  """
  Returns a list of the read lines.
  """
  try:
    return processes[i][PROC_PROC].stdout.read()
  #except Exception as ex:
    #print "% Exception type", type(ex).__name__, " with args", ex.args
  except:
    return ""
  
  
def update_solution(i):
  processes[i][PROC_TIMESOL] = time.time()
  ls = processes[i][PROC_OUT].split("----------\n")[-2:]
  processes[i][PROC_SOL] = ls[0] + "----------"
  processes[i][PROC_OUT] = ls[1]
  for line in processes[i][PROC_SOL].split("\n"):
    if "INT____00041" in line:
      processes[i][PROC_OBJ] = int(replace(replace(line.split(' = ')[1], ';', ''),'\n', ''))
      #print "% Read obj val", processes[i][PROC_OBJ]
      break
     
  
def parallelize(seq_schedule, timeout, no_proc = cpu_count(), timewait = 1, timeobj = 0):
  """
  Parallelizes a sequential schedule according to the number of processors 
  and the timeout.
  """
  inf = float("+inf")
  par_schedule = []
  n = len(seq_schedule)
  i = 0
  rem_time = 0
  if n <= no_proc:
    return [(s, inf, timewait, timeobj) for (s, t) in seq_schedule]
  
  sorted_schedule = sorted(
    schedule, key = lambda x : x[1], reverse = True
  )[0 : no_proc - 1]
  par_schedule = [(s, inf, timewait) for (s, t) in sorted_schedule]
  for (s, t) in [x for x in schedule if x not in sorted_schedule]:
    par_schedule.append([s, timeout * t, timewait, timeobj])
    rem_time += t
  for i in range(no_proc - 1, n):
    par_schedule[i][1] = round(par_schedule[i][1] / rem_time)
  return par_schedule
  
def main():
  inst = '2DPacking.fzn'
  
  seq_schedule = [
    ('/home/jacopo/programmi/constraint_solvers/chuffed/fzn_chuffed -a ' + inst , 600),
    #('/home/jacopo/programmi/constraint_solvers/chuffed/fzn_chuffed -a ' + inst , 600),
    ('/home/jacopo/programmi/minizinc-1.6/bin/fzn_cpx -a ' + inst, 600),
    #('unbuffer flatzinc -a -b lazy ' + inst, 400),
    #('flatzinc -a -b lazy ' + inst, 400),
    ('flatzinc -a -b mip ' + inst, 600)
    #('sh prova.sh', 600)
    #('unbuffer flatzinc -a -b mip ' + inst, 600)
  ]
  par_schedule = parallelize(seq_schedule, 1800, cpu_count())
  
  print "% Running with", cpu_count(), "CPUs"

  proc_count = min(len(par_schedule),cpu_count())
  running_proc = proc_count
  obj = None
  
  for i in range(proc_count):
    (cmd, timeout, timewait, timeobj) = par_schedule.pop()   
    print '% Starting',cmd,'for',timeout,'seconds at', i
    launch_solver(i,cmd, timeout, timewait, timeobj, obj)

  while running_proc > 0:
    best_sol = ""
    time.sleep(SLEEP_TIME)
    
    # Read and parse the outputs.
    for i in processes:
      lines = read_lines(i)
      if len(lines) > 0:
	print "% Process", i, "produced", len(lines), "characters"
      processes[i][PROC_OUT] += lines
      if '----------' in lines:
	update_solution(i)
	#print "%Process", i, ": new solution found with value", processes[i][PROC_OBJ]
	if obj == None or processes[i][PROC_OBJ] < obj:
	  obj = processes[i][PROC_OBJ]
	  print "% Process", i, "found solution with value", processes[i][PROC_OBJ]
	  best_sol = processes[i][PROC_SOL]
      
      if '==========' in lines or '=====UNSATISFIABLE=====' in lines:
	  print '=========='
	  print '% Search completed by', i, ", killing remaing processes"
	  for i in processes:
	    kill_process(processes[i][PROC_PROC])
	  os._exit(0)
     
    #print new solution if any
    if best_sol != "":
      print best_sol

    # Unexpected termination of a solver.
    for i in processes.keys():
      if not processes[i][PROC_PROC].poll() is None:
	  print '% Error:', i, "return with code", processes[i][PROC_PROC].returncode
	  # launch a new solver if any
	  if len(par_schedule) > 0:
	    (cmd, timeout, timewait, timeobj) = par_schedule.pop()
	    print '% Starting',cmd,'for',timeout,'seconds'
	    timeout += processes[i][PROC_TIMEOUT] + processes[i][PROC_START] - time.time()
	    launch_solver(proc_count,cmd, timeout, timewait, timeobj, obj)
	    proc_count +=1
	  else:
	    running_proc -= 1
	  del processes[i]	
	
    # Deal with expired timeouts.
    for i in processes.keys():
      if time.time() - processes[i][PROC_START] > processes[i][PROC_TIMEOUT] and \
	time.time() - processes[i][PROC_TIMESOL] > processes[i][PROC_TIMEWAIT]:
	  print '%', i, 'timeout:'
	  kill_process(processes[i][PROC_PROC])
	  # launch a new solver if any
	  if len(par_schedule) > 0:
	    (cmd, timeout, timewait, timeobj) = par_schedule.pop()
	    print '% Starting',cmd,'for',timeout,'seconds'
	    launch_solver(proc_count,cmd, timeout, timewait, timeobj,obj)
	    proc_count += 1
	  else:
	    running_proc -= 1
	  del processes[i]
          
    # If the current solution is obsolete, stop the process and restart with 
    # the modified FlatZinc.
    if obj != None:
      for i in processes.keys():
	if (processes[i][PROC_RESTART_OBJ] == None or processes[i][PROC_RESTART_OBJ] > obj):
	  if (processes[i][PROC_OBJ] == None or processes[i][PROC_OBJ] > obj) and \
	    time.time() - processes[i][PROC_TIMESOL] > processes[i][PROC_TIMEOBJ]:
	      print '% Re-starting',i,'for',timeout,'seconds'
	      kill_process(processes[i][PROC_PROC])
	      timeout += processes[i][PROC_TIMEOUT] + processes[i][PROC_START] - time.time()
	      launch_solver(proc_count,processes[i][PROC_CMD], timeout,
		    processes[i][PROC_TIMEWAIT], processes[i][PROC_TIMEOBJ],obj)
	      proc_count += 1
	      del processes[i]
  
  print "Execution terminated, all solvers in the schedule run"
  
if __name__ == '__main__':
  main()
