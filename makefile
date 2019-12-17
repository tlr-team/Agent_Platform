
run_am:
	@python3 test_node_am.py

clean:
	@rm -rf log/debug_Kademlia* log/data_* log/bucket_list.log 
	@py3clean .

run_test_am:
	@python3 test/test_client.py

run_sdb:
	@python3 test/test_sdb.py