from neta.network_analysis import *

print("Loading users.")
user_helper = UserHelper()
print("Loading network.")
network_container = NetworkContainer.get_network(directed=True, enable_caching=False)
network = network_container.network
recommendation_engine = Recommendation(network_container)
print("Ready!")
