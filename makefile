
run_am:
	@python test_node_am.py

clean:
	@rm -rf log/debug_Kademlia* log/data_* log/bucket_list.log 

run_test_am:
	@python test/test_client.py

run_sdb:
	@python test/test_sdb.py