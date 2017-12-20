SUNNY-CP 2.2
============

SUNNY-CP: a Parallel CP Portfolio Solver

sunny-cp [5] is a parallel parallel portfolio solver that allows to solve a
Constraint (Satisfaction/Optimization) Problem defined in the MiniZinc language.
It essentially implements the SUNNY algorithm described in [1][2][3] and extends
its sequential version [4] that attended the MiniZinc Challenge 2014 [6].
sunny-cp is built on top of state-of-the-art constraint solvers, including:
Choco, Chuffed, CPX, G12/LazyFD, G12/FD, G12/Gurobi, G12/CBC, Gecode, HaifaCSP,
JaCoP, iZplus, MinisatID, Mistral, Opturion, OR-Tools, Picat. These solvers are 
not included by default in sunny-cp, except for those already included in the 
MiniZinc bundle (i.e., G12/CBC, G12/LazyFD, G12/FD, and Gecode).
However, sunny-cp provides utilities for adding new solvers to the portfolio and
for customizing their settings (see below).

In a nutshell, sunny-cp relies on two sequential steps:

  1. PRE-SOLVING: consists in the parallel execution of a (maybe empty) static
     schedule and the neighborhood computation of underlying k-NN algorithm;

  2. SOLVING: consists in the parallel and cooperative execution of a number of
     the predicted solvers, selected by means of SUNNY algorithm.

sunny-cp won the gold medal in the open track of MiniZinc Challenges 2015, 2016,
and 2017 [6].

AUTHORS
=======

sunny-cp is developed by Roberto Amadini (University of Melbourne) and Jacopo
Mauro (University of Oslo). For any question or information, please contact us:

  roberto.amadini at unimelb.edu.au

          mauro.jacopo  at gmail.com


INSTALLATION WITH DOCKER
========================

To deploy sunny-cp it is possibel to use [Docker](www.docker.com).

sudo docker pull jacopomauro/hyvarrec
sudo docker run -d -p <PORT>:9001 --name hyvarrec_container jacopomauro/hyvarrec

curl -F "-P=gecode" -F "mzn=@test/examples/zebra.mzn" http://localhost:9001/process

sudo docker run --entrypoint="/bin/bash" -i --rm -t sunny

jacopomauro/sunny_cp
sudo docker exec -i -t mycont /bin/bash


Assuming Docker is installed, the first step is running make_docker.py script in
the sunny-cp/docker folder:

  sunny-cp/docker$ python make_docker.py [solver1,solver2,...,solverN]

where solver1,...,solverN is a list of the solvers to include in the portfolio.
Actually, this list must be a sublist of the available solvers.
The first solver of the specified list is assumed to be the backup solver.

The make_docker script generates a corresponding Dockerfile that can be used for
later building and executing the Docker image. However, if you only need the
basic installation there is no need to run the python script: just use the file
base-dockerfile as Dockerfile.

If you are working on a Linux platform, just type:

  sunny-cp/docker$ bash build_docker

for building the Docker image and creating the sunny-cp-docker. Then, assuming
that the PATH environment variable points to sunny-cp/bin, you can run the
sunny-cp-docker command for emulating the sunny-cp solver, e.g.:

  sunny-cp/test/examples$ sunny-cp-docker zebra.mzn

Note that you must be superuser both for building the image and running Docker.
If you want to rebuild a Docker image, make sure that you have removed the old 
one with: 

  sudo docker rmi sunny:docker

For more information, please see the Docker documentation at docs.docker.com


SOLVERS
=======

By default, the portfolio of sunny-cp consists of the solvers included in the
[MiniZinc](http://www.minizinc.org) bundle (2.1.6 version):
* G12/CBC
* G12/LazyFD
* G12/FD
* G12/MPI
* [Gecode](http://www.gecode.org/)
* [Chuffed](https://github.com/geoffchu/chuffed)

Additionally, the default installation comes with the following solvers
publicly available online:
* [OR-Tools](https://code.google.com/p/or-tools/) (version v6.4.4495)
* [Choco](http://choco-solver.org/) (version 4.0.4)
* [Picat](http://picat-lang.org/) CP (version 2.2)
* [Picat](http://picat-lang.org/) SAT (version 2.2)
* [JaCoP](http://jacop.osolpro.com/) (version 4.4)
* [MinisatID](http://dtai.cs.kuleuven.be/krr/software/minisatid) (version 3.11.0)
* [HaifaCSP](http://strichman.net.technion.ac.il/haifacsp/) (version 1.3.0)

We invite the developers interested in adding their solver to sunny-cp to contact us.
Note that the included solvers are treated as black boxes, there is no guarantee
that they are bug free.

Solvers used in the past that are currently not included due to compilation problems
or the fact that are not publicly available/free are:
* [Mistral](http://homepages.laas.fr/ehebrard/mistral.html) (version does not compile)
* [G12/Gurobi](http://www.gurobi.com/) (not free)
* [iZplus](http://www.constraint.org/ja/izc_download.html) (not publicly available)
* [Opturion](http://www.opturion.com) (not free)


sunny-cp provides utilities for adding new solvers to the portfolio and for
customizing their settings.

Note that now there is no more a default portfolio: when not better specified,
the default portfolio consists of the solvers defined in the sunny-cp/solvers
directory. For more details, see the README file in the sunny-cp/solvers folder
and the sunny-cp usage. A part from the solvers already included in MiniZinc 
suite, sunny-cp used also other solvers:






Note that the sunny-cp/docker directory already contains the binaries and the
solver redefitions of a number of freely available and dowloadable solvers.
G12/Gurobi is not publicly available; access has been kindly granted by NICTA
Optimization Research Group of Melbourne (Australia). Note that CPX solver has
been included in the MiniZinc suite until version 1.6, and no longer included
from version 2.0. Opturion is an enhancement of CPX. If you are interested in
using these solvers, please contact directly their developers.

NOTE: sunny-cp is not responsible of buggy solvers. However, the user can check
the soundness of a solution with the option --check-solvers.


BASIC INSTALLATION
==================

Once downloaded the sources, move into sunny-cp folder and run install script:

  sunny-cp$ bash install

This is a minimal installation script that checks the proper installation of
Python (and psutil), MiniZinc, mzn2feat. In addition, it checks the installation
of the constituent solvers (in the corresponding folder) and compiles all the
python sources of sunny-cp. If the installation is successful, the following
message will be printed on standard output:

  --- Everything went well!
  To complete sunny-cp installation just append <PATH_TO_SUNNY-CP>/sunny-cp/bin
  to the PATH environment variable.

Once the PATH variable is set, check the installation by typing the command:

  sunny-cp --help

for printing the help page. Note that the installation process will also create
the file src/pfolio_solvers.py containing an object for each installed solver.





FEATURES
========

During the presolving phase (in parallel with the static schedule execution)
sunny-cp extracts a feature vector of the problem in order to apply the k-NN
algorithm for determining the solvers schedule to be run in the following
solving phase. By default, the feature vector is extracted by mzn2feat tool.
sunny-cp provides the sources of this tool: for its installation, decompress the
mzn2feat-1.2.1.tar.bz2 archive and follow the instruction in the README file of
that folder. The sources of mzn2feat extractor are also available at
https://github.com/CP-Unibo/mzn2feat. Moreover, the user can define its own
extractor by implementing a corresponding class in src/features.py


KNOWLEDGE BASE
==============

The SUNNY algorithm on which sunny-cp relies needs a knowledge base, that
consists of a folder containing the information relevant for the schedule
computation. Unlike the previous knowledge bases, that contained thousands of
instances, now the default knowledge base is far smaller: it consists of 76 CSP
instances and 318 COP instances coming from the MiniZinc challenges 2012--2015.
However, the user has the possibility of defining its own knowledge bases.

The default sunny-cp knowledge base is sunny-cp/kb/mznc1215. Moreover, also the 
knowledge base mznc15 used in the MiniZinc Challenge 2016 is available.
For more details, see the README file in sunny-cp/kb folder.


TESTING
=======

Although a full support for automatic testing is not yet implemented, in the
sunny-cp/test/examples folder there is a number of simple MiniZinc models.
You can run them individually, e.g., by typing:

  test/examples$ sunny-cp zebra.mzn

or alternatively you can test all the models of the folder by typing:

  test/examples$ bash run_examples

The run_examples script also produces output.log and errors.log files in the
test/examples folder, where the standard output/error of the tested models are
respectively redirected.

PREREQUISITES
=============

sunny-cp is tested on 64-bit machines running Ubuntu Operating System, and not
yet fully portable on other platforms. Some of the main requirements are:

+ Python >= 2.x
  https://www.python.org/

+ MiniZinc >= 2.0.13
  # FIXME: MiniZinc >= 2.1.5
  http://www.minizinc.org/

+ mzn2feat >= 1.2.1
  https://github.com/CP-Unibo/mzn2feat

+ psutil >= 2.x
  https://pypi.python.org/pypi/psutil


CONTENTS
========

+ bin       contains the executables of sunny-cp

+ docker    contains the utilities for installing sunny-cp with docker

+ kb        contains the utilities for the knowledge base of sunny-cp

+ src       contains the sources of sunny-cp

+ solvers   contains the utilities for the constituent solvers of sunny-cp

+ test      contains some MiniZinc examples for testing sunny-cp

+ tmp       is aimed at containing the temporary files produced by sunny-cp.



ACKNOWLEDGMENTS
===============

We would like to thank the staff of the Optimization Research Group of NICTA
(National ICT of Australia) for allowing us to use G12/Gurobi, as well as for
granting us the computational resources needed for building and testing sunny-cp.


REFERENCES
==========

  [1]  R. Amadini, M. Gabbrielli, and J. Mauro. SUNNY: a Lazy Portfolio Approach
       for Constraint Solving 2013. In ICLP, 2014.

  [2]  R. Amadini, M. Gabbrielli, and J. Mauro. Portfolio Approaches for
       Constraint Optimization Problems. In LION, 2014.

  [3]  R. Amadini, and P.J. Stuckey. Sequential Time Splitting and Bounds
       Communication for a Portfolio of Optimization Solvers. In CP, 2014.

  [4]  R. Amadini, M. Gabbrielli, and J. Mauro. SUNNY-CP: a Sequential CP
       Portfolio Solver. In SAC, 2015.

  [5]  R. Amadini, M. Gabbrielli, and J. Mauro. A Multicore Tool for Constraint
       Solving. In IJCAI, 2015.

  [6]  MiniZinc Challenge webpage. http://www.minizinc.org/challenge.html
