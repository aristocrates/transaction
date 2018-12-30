"""
Manual transaction simplification system

The algorithm:
1. Take the sum of all debts (+ or -) for all people
    - These are eveyone's centralized debts to the "central node"
2. Merge the central node with the designated payee (transfer everyone's
pairwise debts to this payee); this will be zero sum
3. Use a greedy algorithm to assign people who are net in debt to people
who will net receive money

This gives dumb results in some cases. If A owes 1000 people 1 cent and B
owes A 10 dollars, than this will make B owe 1000 people 1 cent.
"""
import unittest

def update_adjacency_graph(adjacency_graph, debtor, pay_to, amount):
    """
    adjacency_graph:
      first level keys should already point to hashes (for all possible
      keys "person_name", adjacency_graph["person_name"] should be a hash
      {keys: values}, this hash may be empty)
    """
    if debtor not in adjacency_graph.keys():
        adjacency_graph[debtor] = {}
    if pay_to not in adjacency_graph.keys():
        adjacency_graph[pay_to] = {}

    if pay_to in adjacency_graph[debtor].keys():
        assert(debtor in adjacency_graph[pay_to].keys())
        adjacency_graph[debtor][pay_to] += amount
        adjacency_graph[pay_to][debtor] -= amount
    else:
        adjacency_graph[debtor][pay_to] = amount
        adjacency_graph[pay_to][debtor] = -amount

def transaction_adjacency_graph(pairwise_transactions):
    """
    pairwise_transaction:
      List of hashes [{"debtor": "person_who_owes",
                       "pay_to": "name",
                       "amount": int},
                      ...]
      amount must be positive
    returns:
      Undirected weighted adjacency list of debts
      {"person_name_a": {"person_name_b": amount, ...}, ... }
    """
    # get all the people first and set up empty hashes for them all
    all_people = ( {t["debtor"] for t in pairwise_transactions} |
                   {t["pay_to"] for t in pairwise_transactions} )
    adjacency_graph = {k: {} for k in all_people}
    # fill the graph
    for transaction in pairwise_transactions:
        debtor = transaction["debtor"]
        pay_to = transaction["pay_to"]
        amount = transaction["amount"]
        update_adjacency_graph(adjacency_graph, debtor, pay_to, amount)
    return adjacency_graph

def people_and_total_debt(adjacency_graph):
    """
    Returns the list of all people and a hash {"person_name": net_sum_debt}
      If net_sum_debt < 0, then "person_name" should receive money
      If net_sum_debt > 0, then "person_name" owes money overall
    """
    people = adjacency_graph.keys()
    people_to_total_debt = {k: sum(adjacency_graph[k].values())
                            for k in people}
    return (people, people_to_total_debt)

def simplify_transactions(adjacency_graph):
    """
    Accepts a graph encoded as an undirected weighted adjacency list
      {"person_name_a": {"person_name_b": amount, ...}, ... }

    Returns a hash of {"person_name_a": {"person_name_b": amount}}
      where person_name_a pays amount to person_name_b
      amount is always positive
    """
    people, people_to_total_debt = people_and_total_debt(adjacency_graph)
    receivers = [[p, -people_to_total_debt[p]] for p in people
                  if people_to_total_debt[p] < 0]
    givers = [[p, people_to_total_debt[p]] for p in people
               if people_to_total_debt[p] > 0]

    # assign debts
    simplified_debt_hash = {}
    current_receiver = 0
    current_giver = 0
    while current_receiver < len(receivers):
        if givers[current_giver][1] < receivers[current_receiver][1]:
            give_amount  = givers[current_giver][1]
            give_name    = givers[current_giver][0]
            receive_name = receivers[current_receiver][0]
            givers[current_giver][1]       -= give_amount
            receivers[current_receiver][1] -= give_amount
            #simplified_debt_hash[give_name] = {receive_name: give_amount}
            update_adjacency_graph(simplified_debt_hash, give_name, receive_name, give_amount)
            current_giver += 1
        else:
            give_amount  = receivers[current_receiver][1]
            give_name    = givers[current_giver][0]
            receive_name = receivers[current_receiver][0]
            givers[current_giver][1]       -= give_amount
            receivers[current_receiver][1] -= give_amount
            #simplified_debt_hash[give_name] = {receive_name: give_amount}
            update_adjacency_graph(simplified_debt_hash, give_name, receive_name, give_amount)
            current_receiver += 1
    return simplified_debt_hash

class HashTestCase(unittest.TestCase):
    def assertHashesAlmostEqual(self, hash_a, hash_b, places=None, msg=None, delta=None):
        """
        Recursively traverses hashes to ensure that the tree structure is identical
        and that all "leaf" level values are 
        
        Leaf level values must be numeric
        """
        if type(hash_a) is dict:
            self.assertTrue(type(hash_b) is dict)
            keys_a = hash_a.keys()
            keys_b = hash_b.keys()
            self.assertEqual(keys_a, keys_b)
            for key in keys_a:
                self.assertHashesAlmostEqual(hash_a[key], hash_b[key])
        else:
            self.assertFalse(type(hash_b) is dict)
            val_a = hash_a
            val_b = hash_b
            self.assertAlmostEqual(val_a, val_b, places = places, msg = msg, delta = delta)

class TestAdjacency(HashTestCase):
    standard_transactions = [{"debtor": "Kevin", "pay_to": "Xander", "amount": 800},
                             {"debtor": "John", "pay_to": "Xander", "amount": 750},
                             {"debtor": "William", "pay_to": "Xander", "amount": 800},
                             {"debtor": "Xander", "pay_to": "Kevin", "amount": 30},
                             {"debtor": "Kevin", "pay_to": "Xander", "amount": 20},
                             {"debtor": "John", "pay_to": "William", "amount": 100},
                             {"debtor": "William", "pay_to": "Kevin", "amount": 40},
                             {"debtor": "Xander", "pay_to": "John", "amount": 20},
                             {"debtor": "Kevin", "pay_to": "William", "amount": 12.5}]
    standard_actual_total = {"Kevin": 800 - 30 + 20 - 40 + 12.5,
                             "Xander": -800 - 750 - 800 + 30 - 20 + 20,
                             "John": 750 + 100 - 20,
                             "William": 800 - 100 + 40 - 12.5}
    dup_pair_transactions = [{"debtor": "Kevin", "pay_to": "Xander", "amount": 50},
                             {"debtor": "Kevin", "pay_to": "Xander", "amount": 30},
                             {"debtor": "Xander", "pay_to": "Kevin", "amount": 20},
                             {"debtor": "Xander", "pay_to": "Kevin", "amount": 75},
                             {"debtor": "John", "pay_to": "Kevin", "amount": 10},
                             {"debtor": "John", "pay_to": "Kevin", "amount": 14},
                             {"debtor": "Kevin", "pay_to": "John", "amount": 29},
                             {"debtor": "Kevin", "pay_to": "John", "amount": 7}]
    dup_pair_actual_total = {"Kevin": 50 + 30 - 20 - 75 - 10 - 14 + 29 + 7,
                             "Xander": -50 - 30 + 20 + 75,
                             "John": 10 + 14 - 29 - 7}

    def test_standard_transactions(self):
        adjacency_graph = transaction_adjacency_graph(self.standard_transactions)
        people, total_debt = people_and_total_debt(adjacency_graph)
        for p in people:
            self.assertAlmostEqual(total_debt[p], self.standard_actual_total[p])

    def test_dup_pair_transactions(self):
        adjacency_graph = transaction_adjacency_graph(self.dup_pair_transactions)
        people, total_debt = people_and_total_debt(adjacency_graph)
        for p in people:
            self.assertAlmostEqual(total_debt[p], self.dup_pair_actual_total[p])

    def test_conservation_of_money(self):
        pass

class TestSimplify(HashTestCase):
    transactions_single = TestAdjacency.standard_transactions
    single_actual_simplified = {"Kevin": {"Xander": 762.5},
                                "William": {"Xander": 727.5},
                                "John": {"Xander": 830},
                                "Xander": {"Kevin": -762.5, "William": -727.5, "John": -830}}
    transactions_multiple = [{"debtor": "Kevin", "pay_to": "Xander", "amount": 800},
                             {"debtor": "John", "pay_to": "Xander", "amount": 750},
                             {"debtor": "John", "pay_to": "William", "amount": 700},
                             {"debtor": "Kevin", "pay_to": "William", "amount": 800},
                             {"debtor": "Xander", "pay_to": "Kevin", "amount": 30},
                             {"debtor": "Kevin", "pay_to": "Xander", "amount": 20},
                             {"debtor": "John", "pay_to": "William", "amount": 100},
                             {"debtor": "William", "pay_to": "Kevin", "amount": 40},
                             {"debtor": "Xander", "pay_to": "John", "amount": 20},
                             {"debtor": "Kevin", "pay_to": "William", "amount": 12.5}]
    multiple_actual_total_debts = {"Kevin": 800 + 800 - 30 + 20 - 40 + 12.5,
                                   "Xander": -800 - 750 + 30 - 20 + 20,
                                   "John": 750 + 700 + 100 - 20,
                                   "William": -700 - 800 - 100 + 40 - 12.5}

    def test_single_recipient(self):
        adj_graph = transaction_adjacency_graph(self.transactions_single)
        simplified_transactions = simplify_transactions(adj_graph)
        self.assertHashesAlmostEqual(simplified_transactions,
                                     self.single_actual_simplified)

    def test_multiple_recipients(self):
        adj_graph = transaction_adjacency_graph(self.transactions_multiple)
        simplified_transactions = simplify_transactions(adj_graph)
        # verify that total debts match
        # since no guarantees are given on who will be split between paying
        # two people
        for p in self.multiple_actual_total_debts.keys():
            self.assertAlmostEqual(sum(simplified_transactions[p].values()),
                                   self.multiple_actual_total_debts[p])

if __name__=="__main__":
    unittest.main()
