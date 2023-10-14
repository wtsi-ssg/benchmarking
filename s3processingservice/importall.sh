s3cmd ls s3://it-randd/results/ | sed 's/.*results/results/g' | xargs -I{} -- python create_test.py 192.168.3.1 user dumbtemppassword {}
s3cmd ls s3://it-randd/ci_results/ | sed 's/.*ci_results/ci_results/g' | xargs -I{} -- python create_test.py 192.168.3.1 user dumbtemppassword {}
