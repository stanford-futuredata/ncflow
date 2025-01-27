# POP + NCFlow

Code repository for [POP](https://firasabuzaid.com/public/pop.pdf) and [NCFlow](https://www.usenix.org/system/files/nsdi21-abuzaid.pdf). This is originally a fork of the [NCFlow repository](https://github.com/netcontract/ncflow.git) that was created for the NSDI 2021 submission.

Setup validated on Ubuntu 16.04.

Run `download.sh` to fetch the traffic matrices and pre-computed paths used in
our evaluation. (For confidentiality reasons, we only share TMs and paths for
topologies from the Internet Topology Zoo.)

## Dependencies
- Python 3.8 (Anaconda installation recommended)
  - See `environment.yml` for a list of Python library dependencies
  - Run `pip install -r requirements.txt` for additional non-`conda` dependencies
- Gurobi 9.1.2 (Requires a Gurobi license)

