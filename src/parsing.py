'''
sunny-cp: a CP portfolio solver consisting of 12 constituent solvers:

  Choco, Chuffed, CPX, G12/LazyFD, G12/FD, G12/Gurobi, 
  G12/CBC, Gecode, HaifaCSP, iZplus, MinisatID, OR-Tools

********************************************************************************
* Don't forget to properly set the SUNNY_HOME and PATH environment variables!! *
********************************************************************************
  
Usage: sunny-cp [OPTIONS] <MODEL.mzn> [DATA.dzn] 

Options:

  -h, --help
    Print this message
    
  -T <TIMEOUT>
    #FIXME: Update this.
    Timeout (in seconds) of SUNNY algorithm. Note that this IS NOT the timeout 
    of the whole solving process: if the instance is still not solved within T 
    seconds by the scheduled solvers, the others non-scheduled solvers of the 
    portfolio will be executed for T seconds following a default ordering. 
    Anyway, note that none of the solvers will be executed for more than T 
    seconds.
    The default value is T = 1800, while the default 'backup' ordering is:
      chuffed, g12cpx, minisatid, gecode, g12lazyfd, g12fd, g12gurobi, g12cbc    
  
  -k <SIZE>
    Neighborhood size of SUNNY underlying k-NN algorithm. The default value of 
    k is 70, while the distance metric is the Euclidean one
  
  -P <PORTFOLIO>
    Specifies the portfolio through a comma-separated list of solvers of the 
    form s_1,s_2,...,s_m. Note that such solvers must be a not empty subset of 
    the default portfolio. Moreover, also the specified ordering of solvers is 
    important: indeed, in case of failure of the scheduled solvers, the other 
    solvers will be executed according to such ordering. This option can be used 
    to select a particular sub-portfolio or even to change the default ordering 
    of the solvers in case of failures
  
  -b <SOLVER>
    Set the backup solver of the portfolio. It must belong to the specified 
    portfolio. The default backup solver is chuffed
    
  -K <PATH>
    Absolute path of the folder which contains the knowledge base. The default 
    knowledge base is in SUNNY_HOME/kb/all_T1800. For more details, see the 
    README file in SUNNY_HOME/kb folder
  
  -s <SCHEDULE>
    # FIXME: Update this.
    Specifies a static schedule to be run before executing the SUNNY algorithm 
    on a given COP. The schedule must be passed in the form: 
      s_1,t_1,s_2,t_2,...,s_m,t_m
    where each s_i belongs to the specified portfolio, 0 < t_i < T, and 
    C = t_1 + ... + t_m <= T, where T is the specified solving timeout for COPs. 
    Passing a static schedule has the purpose of providing a 'warm start' to the 
    SUNNY algorithm in the first C seconds: first s_1 is run for t_1 seconds, 
    then s_2 is run for t_2 seconds, ..., and finally s_m is run for t_m seconds 
    by exploiting each sub-optimal solution found by the previous solver. If the 
    problem is still not solved after running the static schedule, the schedule 
    resulting from SUNNY algorithm is run in the remaining T - C seconds. The 
    static schedule is empty by default
    
  -d <PATH> 
    Absolute path of the folder in which the temporary files created by the 
    solver will be put. The default directory is SUNNY_HOME/tmp, and by default 
    such files are deleted after sunny-cp execution
    
  -e <EXTRACTOR>
    Features extractor used by sunny-cp. By default is mzn2feat, but it can be 
    changed by defining a corresponding class in SUNNY_HOME/src/features.py
    
  -p <CORES>
    The number of cores to use in the solving process. By default, is the number 
    of CPUs in the system
    
  --fzn-options "<OPTIONS>"
    Allows to run each scheduled solver on its specific FlatZinc model by using 
    the options specified in <OPTIONS> string. No checks are performed on that 
    string. By default, the options string is empty for CSPs, while is "-a" for 
    COPs. Note that this option should allow to print all the solutions of the 
    problem according to the MiniZinc Challenge rules.
  --fzn-options-<SOLVER_NAME> "<OPTIONS>"
    Runs the solver <SOLVER_NAME> with the options specified in <OPTIONS>
  
  -a
    For compatibility with MiniZinc Challenge rules. This option is equivalent 
    to --fzn-options "-a". By default, this flag is unset for CSPs while is set 
    for COPs
  
  -f
    For compatibility with MiniZinc Challenge rules. This option is deprecated 
    since it is always ignored: use --fzn-options "-f" instead

  --wait-time <TIME>
    Don't stop each running solver if it has produced a solution in the last 
    <TIME> seconds (only for COPs). By default, <TIME> is 2 seconds. Also the 
    the constant +inf is allowed
  --wait-time-<SOLVER> <TIME>
    Don't stop <SOLVER> if it has produced a solution in the last <TIME> seconds
  
  --restart-time <TIME>
    Restart each constituent solver if its best solution is obsolete and it has 
    not produced a solution in the last <TIME> seconds (only for COPs). 
    By default, <TIME> is 5 seconds. Also the constant +inf is allowed
  --restart-time-<SOLVER> <TIME>
    Restart <SOLVER> if its best solution is obsolete and it has not produced a 
    solution in the last <TIME> seconds
    
  -x <AUX_VAR>
    Specifies the name of the auxiliary variable used for tracking the objective 
    function value (for COPs). Note that such variable must not appear in the 
    MiniZinc model to be solved. The default variable name is o__b__j__v__a__r
    
  --g12
    Use just the solvers of G12 platform, by using g12cpx as the backup solver. 
    This is equivalent to set -P g12cbc,g12cpx,g12fd,g12lazyfd and -b g12cpx
    
  --keep
    Do not erase the temporary files created by the solver and stored in the 
    specified directory (useful for debugging). This option is unset by default
    
  --csp-<OPTION> <VALUE>
    Allows to set the specific option only if the input problem is a CSP. Note 
    that the '-' character of <OPTION> must be omitted
    For example, --csp-T 900 set the T parameter to 900 only if the problem is a 
    CSP, while such option is ignored for COPs
    
  --cop-<OPTION> <VALUE>
    Allows to set the specific option only if the input problem is a COP. Note 
    that the '-' character of <OPTION> must be omitted.
    For example, --cop-T 900 set the T parameter to 900 only if the problem is a 
    COP, while such option is ignored for CSPs
'''

import sys
import getopt
from string   import replace
from defaults import *
from features import *
from problem  import *
  
def parse_arguments(args):
  """
  Parse the input arguments and returns the corresponding values.
  """
  
  # Get the arguments and parse the input model to get auxiliary information. 
  mzn, dzn, opts = get_args(args)
  k, timeout, pfolio, backup, kb, lims, \
  static, solve, obj_expr, mzn_out = parse_model(mzn)
  extractor = eval(DEF_EXTRACTOR)
  cores = DEF_CORES
  tmp_dir = DEF_TMP_DIR
  keep = DEF_KEEP
  wait_time = DEF_WAIT_TIME
  restart_time = DEF_RESTART_TIME
  aux_var = DEF_AUX_VAR
  if solve == 'sat':
    solver_options = dict((s, {
      'options': DEF_OPTIONS_CSP, 
      'wait_time': DEF_WAIT_TIME, 
      'restart_time': DEF_RESTART_TIME
      }) for s in DEF_PFOLIO_CSP
    )
  else:
    solver_options = dict((s, {
      'options': DEF_OPTIONS_COP, 
      'wait_time': DEF_WAIT_TIME, 
      'restart_time': DEF_RESTART_TIME
      }) for s in DEF_PFOLIO_COP
    )
  
  # Arguments parsing.
  for o, a in opts:
    if o in ('-h', '--help'):
      print __doc__
      sys.exit(0)
    elif o == '-p':
      n = int(a)
      if n < 1:
        print >> sys.stderr, 'Warning: -p parameter set to 1.'
        cores = 1
      elif n > cores:
        print >> sys.stderr, 'Warning: -p parameter set to',cores
      else:
        cores = n
    elif o == '-e':
      extractor = eval(a)
    elif o == '-k':
      k = int(a)
      if k < 0:
        print >> sys.stderr, 'Error! Negative value ' + a + ' for k value.'
        print >> sys.stderr, 'For help use --help'
        sys.exit(2)
    elif o == '-T':
      timeout= int(a)
      if timeout<= 0:
        print >> sys.stderr, 'Error! Non-positive value ' + a + ' for timeout.'
        print >> sys.stderr, 'For help use --help'
        sys.exit(2)
    elif o == '-P':
      p = a.split(',')
      if not p:
        print >> sys.stderr, 'Error! The portfolio ' + a + ' is not valid.'
        print >> sys.stderr, 'For help use --help'
        sys.exit(2)
      if not set(p) <= set(pfolio):
        print >> sys.stderr, 'Error! The portfolio',a,'is not a subset of', \
          str(pfolio)
        print >> sys.stderr, 'For help use --help'
        sys.exit(2)
      pfolio = p
    elif o == '-b':
      backup = a
    elif o == '-K':
      if not os.path.exists(a):
        print >> sys.stderr, 'Error! Directory ' + a + ' not exists.'
        print >> sys.stderr, 'For help use --help'
        sys.exit(2)
      name = [token for token in a.split('/') if token][-1]
      if a[-1] != '/':
        path = a + '/'
      else:
        path = a
      if solve in ['min', 'max']:
        pb = 'cop'
      else:
        pb = 'csp'
      kb = path + 'kb_' + pb + '_' + name
      lims = path + 'lims_' + pb + '_' + name
      if not os.path.exists(kb):
        print >> sys.stderr, 'Error! File ' + kb + ' not exists.'
        print >> sys.stderr, 'For help use --help'
        sys.exit(2)
      if not os.path.exists(lims):
        print >> sys.stderr, 'Error! File ' + kb + ' not exists.'
        print >> sys.stderr, 'For help use --help'
        sys.exit(2)
    elif o == '-s':
      s = a.split(',')
      for i in range(0, len(s) / 2):
        static.append((s[2 * i], int(s[2 * i + 1])))
    elif o == '-d':
      if not os.path.exists(a):
        print >> sys.stderr, 'Error! Directory ' + a + ' not exists.'
        print >> sys.stderr, 'For help use --help'
        sys.exit(2)
      name = [token for token in a.split('/') if token][-1]
      if a[-1] == '/':
        tmp_dir = a[0 : -1]
      else:
        tmp_dir = a
    elif o == '-a':
      for item in solver_options.values():
        item['options'] = '-a'
    elif o.startswith('--fzn-options'):
      if len(o) > 13:
        solver = o[14:]
        solver_options[solver]['options'] = a
      else:
	for item in solver_options.values():  
	  item['options'] = a
    elif o.startswith('--wait-time'):
      wait_time = float(a)
      if wait_time < 0:
        print >> sys.stderr, 'Error! Not acceptable negative time'
        print >> sys.stderr, 'For help use --help'
        sys.exit(2)
      if len(o) > 11:
	solver = o[12:]
	solver_options[solver]['wait_time'] = wait_time
      else:
        for item in solver_options.values():  
	  item['wait_time'] = a
    elif o.startswith('--restart-time'):
      rest_time = float(a)
      if rest_time < 0:
        print >> sys.stderr, 'Error! Not acceptable negative time'
        print >> sys.stderr, 'For help use --help'
        sys.exit(2)
      if len(o) > 14:
	solver = o[15:]
	solver_options[solver]['restart_time'] = rest_time
      else:
        for item in solver_options.values():  
	  item['restart_time'] = a
    elif o == '-x':
      aux_var = a
    elif o == '--keep':
      keep = True
    elif o == '--g12':
      pfolio = ['g12cbc', 'g12cpx', 'g12fd', 'g12lazyfd']
      backup = 'g12cpx'
    elif o.startswith('--csp-') and solve == 'sat' or \
         o.startswith('--cop-') and solve != 'sat':
	   if len(o) == 7:
             opts.append(['-' + o[6], a])
           else:
	     opts.append(['--' + o[6:], a])
           
  # Additional checks.
  if backup not in pfolio:
    print >> sys.stderr, \
    'Error! Backup solver ' + backup + ' is not in ' + str(pfolio)
    print >> sys.stderr, 'For help use --help'
    sys.exit(2)
  if not (set(s for (s, t) in static) <= set(pfolio)):
    print >> sys.stderr, \
    'Error! Static schedule is not a subset of ' + str(pfolio)
    print >> sys.stderr, 'For help use --help'
    sys.exit(2)
  st = 0
  for (s, t) in static:
    st += t
    if t <= 0 or t >= timeout:
      print >> sys.stderr, 'Error! Not valid time slot',t,'for static schedule'
      print >> sys.stderr, 'For help use --help'
      sys.exit(2)
    if s not in pfolio:
      print >> sys.stderr, 'Error! Solver ' + s + ' is not in ' + str(pfolio)
      print >> sys.stderr, 'For help use --help'
      sys.exit(2)
  if st > timeout:
    print >> sys.stderr, \
    'Error! Static schedule allocated time exceeds the timeout'
    print >> sys.stderr, 'For help use --help'
    
  problem = Problem(mzn, dzn, mzn_out, solve, obj_expr, aux_var)
  return problem, k, timeout, pfolio, backup, kb, lims, static, extractor, \
    cores, solver_options, tmp_dir, keep

def get_args(args):
  """
  Get the arguments.
  """
  dzn = ''
  try:
    options = ['T', 'k', 'P', 'b', 'K', 's', 'd', 'p', 'e', 'x', 'a', 'f']
    long_options = ['fzn-options', 'wait-time', 'restart-time']
    long_options += [o + '-' + s for o in long_options for s in DEF_PFOLIO_CSP]
    csp_opts = ['csp-' + o + '=' for o in options + long_options]
    cop_opts = ['cop-' + o + '=' for o in options + long_options]
    long_options = [o + '=' for o in long_options]
    long_options += ['help', 'keep', 'g12'] + csp_opts + cop_opts
    opts, args = getopt.getopt(
      args, 'hafT:k:P:b:K:s:d:p:e:x:', long_options
    )
  except getopt.error, msg:
    print msg
    print >> sys.stderr, 'For help use --help'
    sys.exit(2)
  
  if len(args) == 0:
    for o, a in opts:
      if o in ('-h', '--help'):
        print __doc__
        sys.exit(0)
    print >> sys.stderr, 'Error! No arguments given.'
    print >> sys.stderr, 'For help use --help'
    sys.exit(2)
  mzn = args[0]
  if not mzn.endswith('.mzn'):
    print >> sys.stderr, 'Error! MiniZinc input model must have .mzn extension.'
    print >> sys.stderr, 'For help use --help'
    sys.exit(2)
  if len(args) > 1:
    dzn = args[1]
    if not dzn.endswith('.dzn'):
      print >> sys.stderr, \
      'Error! MiniZinc input data must have .dzn extension.'
      print >> sys.stderr, 'For help use --help'
      sys.exit(2)
  return mzn, dzn, opts

def parse_model(mzn):
  """
  Parse the input model to get auxiliary information (e.g., objective function).
  """
  # Set default arguments.
  k = DEF_K_CSP
  timeout= DEF_TOUT_CSP
  pfolio = DEF_PFOLIO_CSP
  backup = DEF_BACKUP_CSP
  kb = DEF_KB_CSP
  lims = DEF_LIMS_CSP
  static = DEF_STATIC_CSP
  solve = 'sat'
  solve_item = False
  output_item = False
  include_list = [mzn]
  mzn_out = None
  static = []
  obj_expr = ''
  mzn_dir = os.path.dirname(mzn)
  
  # Possibly extract solve and output items (for COPs).
  while include_list and not (solve_item and output_item):
    model = include_list.pop()
    if os.path.exists(model):
      lines = open(model, 'r').read().split(';')
    elif os.path.exists(mzn_dir + '/' + model):
      model = mzn_dir + '/' + model
      lines = open(model, 'r').read().split(';')
    else:
      continue
    for line in lines:
      include = False
      new_line = ''
      ignore = False
      for l in line:
        # Ignore comments.
        if ignore or l == '%':
          ignore = True
          if l == '\n':
            ignore = False
        else:
          new_line += l
      tokens = new_line.split()
      i = 0
      for token in tokens:
        if token == 'include' or token == 'include"':
          include = True
        # Looking for included models.
        if include and token[-1] == '"' or token[-1] == '";':
          include = \
            replace(replace(replace(token, 'include"', ''),'"', ''), "'", '')
          include_list.append(include)
          include = False
        elif token.endswith('satisfy'):
          include_list = []
          break
        elif token in ['minimize', 'maximize']:
          solve_item = True
          k = DEF_K_COP
          timeout= DEF_TOUT_COP
          pfolio = DEF_PFOLIO_COP
          backup = DEF_BACKUP_COP
          kb = DEF_KB_COP
          lims = DEF_LIMS_COP
          static = DEF_STATIC_COP
          if token == 'minimize':
            solve = 'min'
          else:
            solve = 'max'
          obj_expr = ''
          for j in range(i + 1, len(tokens)):
            obj_expr += tokens[j] + ' '
          if output_item:
            include_list = []
            break
        elif token in ['output', 'output[']:
          mzn_out = model
          output_item = True
          if solve_item:
            include_list = []
            break
        i += 1
  return k, timeout, pfolio, backup, kb, lims, static, solve, obj_expr, mzn_out