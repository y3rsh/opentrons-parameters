# Tools

1. In this repository directory
1. `cp your_paths_example.py your_paths.py`
1. edit `your_paths.py` to point to the correct path of the protocol on your machine
1. do you want to analyze with different rtp values or a CSV RTP file?
1. generate the rtp values file `/opt/opentrons/resources/python/bin/python3 tools/gen_param_json.py`
1. edit the rtp values files to try analyzing with values other than the default
1. analyze `/opt/opentrons/resources/python/bin/python3 tools/analyze.py`
