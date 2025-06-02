import asyncio
import logging
from dht_node import DHTNode

async def main():
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Create first node (bootstrap node)
    node1 = DHTNode(port=8788)
    await node1.start()
    
    # Create second node and connect it to the first one
    node2 = DHTNode(port=8789)
    await node2.start()
    await node2.join_network(node1.onion_address)
    
    # Store data through the first node
    test_data = b"Hello, anonymous DHT world!"
    file_hash = await node1.store_file(test_data)
    logging.info(f"File stored with hash: {file_hash}")
    
    # Search data through the second node
    found_data = await node2.find_file(file_hash)
    if found_data:
        data, salt = found_data
        logging.info(f"Data found: {data.decode()}")
    else:
        logging.error("Data not found")
    
    # Stop nodes
    await node1.stop()
    await node2.stop()

if __name__ == "__main__":
    asyncio.run(main()) 