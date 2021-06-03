# ECS 152A Yulin Chien, Ethernet-simulation project
import simpy
import math
import numpy as np
import matplotlib.pyplot as plt
import random
import sys
# First  define some global variables. You should change values

class G:
    RANDOM_SEED = 33
    SIM_TIME = 100000  # This should be large
    SLOT_TIME = 1
    N = 30
    # 0.01,0.02,0.03,0.04
    # 0.0005, 0.001, 0.003, 0.005, 0.007, 0.009
    # 0.0005, 0.001, 0.003, 0.005, 0.007, 0.009, 0.01,0.02,0.03,0.04   <-- dataset used for graph
    ARRIVAL_RATES = [] 
    #"pp", "op", "beb","lb" <-- all policies
    RETRANMISSION_POLICIES = [] 
    LONG_SLEEP_TIMER = 1000000000


def p_persistent(self, nodes, curr_slot): 

    for node in nodes: 
        new_slot = np.random.geometric(p=0.5)
        self.dictionary_of_nodes[node].retransmit_slotnum = curr_slot + new_slot

def o_persistent(self, nodes, curr_slot):

    for node in nodes: 
        new_slot = np.random.geometric(p=(1/G.N))
        self.dictionary_of_nodes[node].retransmit_slotnum = curr_slot + new_slot

def bin_exp_backoff(self, nodes, curr_slot):

    for node in nodes:
        # 0 <= r <= 2**K, where k = min(n, 10)
        K = min(self.dictionary_of_nodes[node].reattempt_count, 10)
        self.dictionary_of_nodes[node].retransmit_slotnum = curr_slot + np.random.randint((2**K) + 1) + 1
        self.dictionary_of_nodes[node].reattempt_count += 1


def lin_backoff(self, nodes, curr_slot):
    
    for node in nodes:
        # 0 <= r <= K,  where  K = min (n,1024)
        K = min(self.dictionary_of_nodes[node].reattempt_count, 1024)
        self.dictionary_of_nodes[node].retransmit_slotnum = curr_slot + np.random.randint(K + 1) + 1
        self.dictionary_of_nodes[node].reattempt_count += 1
        
 

        
class Server_Process(object):
    def __init__(self, env, dictionary_of_nodes, retran_policy, slot_stat):
        self.env = env
        self.dictionary_of_nodes = dictionary_of_nodes 
        self.retran_policy = retran_policy 
        self.slot_stat = slot_stat
        self.current_slot = 0
        self.action = env.process(self.run())
            
    def run(self):

        while True: 

            total_transmitting_data = 0

            yield self.env.timeout(G.SLOT_TIME)

            self.current_slot += 1
            trans_nodes = []

            for node in range(1,len(self.dictionary_of_nodes)+1):
                if self.dictionary_of_nodes[node].packet_count > 0 and self.dictionary_of_nodes[node].retransmit_slotnum == self.current_slot:
                    total_transmitting_data += 1
                    trans_nodes.append(node)

            self.slot_stat.addNumber(total_transmitting_data)

            # if nodes transmitting = 0 or 1 do nothing , only do sth when there is collision
            if total_transmitting_data > 1:
            
                if self.retran_policy == "pp":
                    p_persistent(self, trans_nodes, self.current_slot)
                    
                elif self.retran_policy == "op":
                    o_persistent(self, trans_nodes, self.current_slot)

                elif self.retran_policy == "beb":
                    bin_exp_backoff(self, trans_nodes, self.current_slot)
                                     
                elif self.retran_policy == "lb":
                    lin_backoff(self, trans_nodes, self.current_slot)

            elif total_transmitting_data == 1 and len(trans_nodes) == 1:

                self.dictionary_of_nodes[trans_nodes[0]].packet_count -= 1 
                self.dictionary_of_nodes[trans_nodes[0]].retransmit_slotnum = self.current_slot + 1
                self.dictionary_of_nodes[trans_nodes[0]].reattempt_count = 0

            #reset array/T_T_D
            trans_nodes.clear() 
            total_transmitting_data = 0
        
class Node_Process(object): 
    def __init__(self, env, id, arrival_rate):
        
        self.env = env
        self.id = id
        self.arrival_rate = arrival_rate
        self.packet_count = 0
        self.reattempt_count = 0
        self.retransmit_slotnum = 0

        self.action = env.process(self.run())

    def run(self):
        # packet arrivals 
        
        #print("Arrival Process Started:", self.id)   
        while True:

            yield self.env.timeout(random.expovariate(self.arrival_rate))

            if self.packet_count == 0:
                self.retransmit_slotnum = math.ceil(self.env.now)
            
            self.packet_count += 1
   

class Packet:
    def __init__(self, identifier, arrival_time):
        self.identifier = identifier
        self.arrival_time = arrival_time


class StatObject(object):    
    def __init__(self):
        self.dataset =[]

    def addNumber(self,x):
        self.dataset.append(x)


# Note To Grader: If you want to all values in the graph change ARRIVAL_RATES and RETRAMSMISSION_POLICIES in class G to the values mentioned above them "<--"
# Comment out lines 152 to 160 , and ,  208 to 209
# Uncomment Code to plot starting from line 211.  And uncomment lines 194 to 195 for clearer printing data. Thank you! 


def main():

    if len(sys.argv) != 4:
        sys.exit("Please enter with format:  python ethernet-simulation.py 25 pp 0.001")
        
    elif sys.argv[2] not in ('pp','op','beb','lb'):
        sys.exit(sys.argv[2] + " is not a valid algorithm, Choices are: pp, op, beb, lb")
    
    G.N = int(sys.argv[1]) 
    G.RETRANMISSION_POLICIES.append(sys.argv[2])
    G.ARRIVAL_RATES.append(float(sys.argv[3]))
        
    #print("Simiulation Analysis of Random Access Protocols")
    pp_a = []
    op_a = []
    beb_a = []
    lb_a = []


    random.seed(G.RANDOM_SEED)

    for retran_policy in G.RETRANMISSION_POLICIES: 
        
        for arrival_rate in G.ARRIVAL_RATES:
            env = simpy.Environment()
            slot_stat = StatObject()
            dictionary_of_nodes  = {} # I chose to pass the list of nodes as a 
                                      # dictionary since I really like python dictionaries :)
            
            for i in list(range(1,G.N+1)):
                node = Node_Process(env, i, arrival_rate)
                dictionary_of_nodes[i] = node
            server_process = Server_Process(env, dictionary_of_nodes,retran_policy,slot_stat)
            env.run(until=G.SIM_TIME)


            data = slot_stat.dataset.count(1)

            throughput = data/server_process.current_slot

            output_data = round(throughput,2)
            output_data = "{:.2f}".format(output_data)
            print("Throughput: " + str(output_data))
            # print("Number of Nodes:" + str(G.N) + ", Retransmission Policy:" + retran_policy +
            # ", Arrival rate:" + str(arrival_rate) + ",  Throughput:" + str(output_data))

            if retran_policy == "pp":
                pp_a.append(throughput)
            elif retran_policy == "op":
                op_a.append(throughput)
            elif retran_policy == "beb":
                beb_a.append(throughput)
            elif retran_policy == "lb":
                lb_a.append(throughput)
            
        

    G.RETRANMISSION_POLICIES.clear()
    G.ARRIVAL_RATES.clear()
    
    # code to plot 
    # x_axis = []
    # for lamb in G.ARRIVAL_RATES:
    #     NT_Lambda = round((lamb * G.N), 2)
    #     x_axis.append(NT_Lambda)

    # x_1 = np.asarray(x_axis)
    # y_1 = np.asarray(pp_a)
    # plt.plot(x_1, y_1, label="pp")

    # x_2 = np.asarray(x_axis)
    # y_2 = np.asarray(op_a)
    # plt.plot(x_2, y_2, label="op")

    # x_3 = np.asarray(x_axis)
    # y_3 = np.asarray(beb_a)
    # plt.plot(x_3, y_3, label="beb")

    # x_4 = np.asarray(x_axis)
    # y_4 = np.asarray(lb_a)
    # plt.plot(x_4, y_4, label="lb")

    # plt.xlabel("Offered Load (Lambda * N)")
    # plt.ylabel("Achieved Throughput (Fraction of Successful Slots)")
    # plt.title("Ethernet Simulation Results")
    # plt.grid()
    # plt.legend()
    # plt.show()
        

        
           
    
if __name__ == '__main__': main()
