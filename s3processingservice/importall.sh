s3cmd ls s3://it_randd/ci_results/ | sed 's/.*ci_results/ci_results/g' | xargs -I{} -- python create_test.py 192.168.3.1 user MxRwazxoAhn55aicDK9T7SPU6YAOhosqLK60SYxAPBM= {}
