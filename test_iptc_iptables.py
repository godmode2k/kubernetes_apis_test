# -------------------------------------------------------------------
# Purpose: iptables - NAT Port-forwarding test
# Author: Ho-Jung Kim (godmode2k@hotmail.com)
# Date: Since August 04, 2022
#
# Reference:
# python-iptables: iptc
#  - https://github.com/ldx/python-iptables
#  - https://python-iptables.readthedocs.io/en/latest/examples.html
# port range
#  - https://stackoverflow.com/questions/33052149/is-it-possible-to-map-11-port-range-iptable-dnat-rules
#  - http://git.netfilter.org/iptables/commit/?id=36976c4b54061b0147d56892ac9d402dae3069df
# https://www.systutorials.com/port-forwarding-using-iptables/
#
# $ pip install python-iptables
#
# License:
#
#*
#* Copyright (C) 2022 Ho-Jung Kim (godmode2k@hotmail.com)
#*
#* Licensed under the Apache License, Version 2.0 (the "License");
#* you may not use this file except in compliance with the License.
#* You may obtain a copy of the License at
#*
#*      http://www.apache.org/licenses/LICENSE-2.0
#*
#* Unless required by applicable law or agreed to in writing, software
#* distributed under the License is distributed on an "AS IS" BASIS,
#* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#* See the License for the specific language governing permissions and
#* limitations under the License.
#*
# -------------------------------------------------------------------



# pip install python-iptables
# SEE: https://github.com/ldx/python-iptables
import iptc


'''
// NAT Port-forwarding
client <-> A: (private) 10.0.2.15 <-> B: (private) 10.0.2.4 <-> C: Worker Node: (private) IP:Port (Service: Web, DB, ...)



1. test #1
client <-> A <-> B

----------------------------------
A: 10.0.2.15:8085 -> B: 10.0.2.4:8085
----------------------------------
sudo iptables -t nat -I PREROUTING -p tcp --dport 8085 -j DNAT --to-destination 10.0.2.4:8085
sudo iptables -t nat -A POSTROUTING -p tcp --dport 8085 -j SNAT --to-source 10.0.2.15
sudo iptables -I INPUT -p tcp --dport 8085 -j ACCEPT
sudo iptables -I FORWARD -j ACCEPT
sudo iptables -I FORWARD -m state -p tcp --dport 8085 --state NEW,RELATED,ESTABLISHED -j ACCEPT
-
sudo iptables -t nat -D PREROUTING -p tcp --dport 8085 -j DNAT --to-destination 10.0.2.4:8085
sudo iptables -t nat -D POSTROUTING -p tcp --dport 8085 -j SNAT --to-source 10.0.2.15
sudo iptables -D INPUT -p tcp --dport 8085 -j ACCEPT
sudo iptables -D FORWARD -j ACCEPT
sudo iptables -D FORWARD -m state -p tcp --dport 8085 --state NEW,RELATED,ESTABLISHED -j ACCEPT

//sudo iptables -I FORWARD -p tcp --dport 8085 -j ACCEPT
//sudo iptables -I FORWARD -m state -p tcp --dport 8085 -d 10.0.2.4 --state NEW,RELATED,ESTABLISHED -j ACCEPT


----------------------------------
B: 10.0.2.4:8085
----------------------------------
sudo iptables -I INPUT -p tcp --dport 8085 -j ACCEPT
-
sudo iptables -D INPUT -p tcp --dport 8085 -j ACCEPT



--------------------------------------------------------------------



2. test #2
client <-> A <-> B <-> C (10.0.2.5)

----------------------------------
A: 10.0.2.15:32579 -> B: 10.0.2.4:32579
----------------------------------
sudo iptables -t nat -I PREROUTING -p tcp --dport 32579 -j DNAT --to-destination 10.0.2.4:32579
sudo iptables -t nat -A POSTROUTING -p tcp --dport 32579 -j SNAT --to-source 10.0.2.15
sudo iptables -I INPUT -p tcp --dport 32579 -j ACCEPT
sudo iptables -I FORWARD -j ACCEPT
sudo iptables -I FORWARD -m state -p tcp --dport 32579 --state NEW,RELATED,ESTABLISHED -j ACCEPT
-
sudo iptables -t nat -D PREROUTING -p tcp --dport 32579 -j DNAT --to-destination 10.0.2.4:32579
sudo iptables -t nat -D POSTROUTING -p tcp --dport 32579 -j SNAT --to-source 10.02.15
sudo iptables -D INPUT -p tcp --dport 32579 -j ACCEPT
sudo iptables -D FORWARD -j ACCEPT
sudo iptables -D FORWARD -m state -p tcp --dport 32579 --state NEW,RELATED,ESTABLISHED -j ACCEPT


----------------------------------
B: 10.0.2.4:32579 -> C: 10.0.2.5:32579
----------------------------------
sudo iptables -t nat -I PREROUTING -p tcp --dport 32579 -j DNAT --to-destination 10.0.2.5:32579
sudo iptables -t nat -A POSTROUTING -p tcp --dport 32579 -j SNAT --to-source 10.0.2.4
sudo iptables -I INPUT -p tcp --dport 32579 -j ACCEPT
sudo iptables -I FORWARD -j ACCEPT
sudo iptables -I FORWARD -m state -p tcp --dport 32579 --state NEW,RELATED,ESTABLISHED -j ACCEPT
-
sudo iptables -t nat -D PREROUTING -p tcp --dport 32579 -j DNAT --to-destination 10.0.2.5:32579
sudo iptables -t nat -D POSTROUTING -p tcp --dport 32579 -j SNAT --to-source 10.0.2.4
sudo iptables -D INPUT -p tcp --dport 32579 -j ACCEPT
sudo iptables -D FORWARD -j ACCEPT
sudo iptables -D FORWARD -m state -p tcp --dport 32579 --state NEW,RELATED,ESTABLISHED -j ACCEPT



--------------------------------------------------------------------



3. port range (30000 ~ 32767)
client <-> A <-> B <-> C (10.0.2.5:32579)

----------------------------------
A: 10.0.2.15:32579 -> B: 10.0.2.4:32579
----------------------------------
sudo iptables -t nat -I PREROUTING -p tcp --dport 30000:32767 -j DNAT --to-destination 10.0.2.4:30000-32767/30000
sudo iptables -t nat -A POSTROUTING -p tcp --dport 30000:32767 -j SNAT --to-source 10.0.2.15
sudo iptables -I INPUT -p tcp --dport 30000:32767 -j ACCEPT
sudo iptables -I FORWARD -j ACCEPT
sudo iptables -I FORWARD -m state -p tcp --dport 30000:32767 --state NEW,RELATED,ESTABLISHED -j ACCEPT
-
sudo iptables -t nat -D PREROUTING -p tcp --dport 30000:32767 -j DNAT --to-destination 10.0.2.4:30000-32767/30000
sudo iptables -t nat -D POSTROUTING -p tcp --dport 30000:32767 -j SNAT --to-source 10.0.2.15
sudo iptables -D INPUT -p tcp --dport 30000:32767 -j ACCEPT
sudo iptables -D FORWARD -j ACCEPT
sudo iptables -D FORWARD -m state -p tcp --dport 30000:32767 --state NEW,RELATED,ESTABLISHED -j ACCEPT

----------------------------------
B: 10.0.2.4:32579 -> C: 10.0.2.5:32579
----------------------------------
sudo iptables -I FORWARD -j ACCEPT
-
sudo iptables -D FORWARD -j ACCEPT
//
sudo iptables -t nat -I PREROUTING -p tcp --dport 32579 -j DNAT --to-destination 10.0.2.5:32579
sudo iptables -t nat -A POSTROUTING -p tcp --dport 32579 -j SNAT --to-source 10.0.2.4
sudo iptables -I INPUT -p tcp --dport 32579 -j ACCEPT
sudo iptables -I FORWARD -m state -p tcp --dport 32579 --state NEW,RELATED,ESTABLISHED -j ACCEPT
-
sudo iptables -t nat -D PREROUTING -p tcp --dport 32579 -j DNAT --to-destination 10.0.2.5:32579
sudo iptables -t nat -D POSTROUTING -p tcp --dport 32579 -j SNAT --to-source 10.0.2.4
sudo iptables -D INPUT -p tcp --dport 32579 -j ACCEPT
sudo iptables -D FORWARD -m state -p tcp --dport 32579 --state NEW,RELATED,ESTABLISHED -j ACCEPT
'''



# Server #1
# ----------------------------------------


# sudo iptables -t nat -I PREROUTING -p tcp --dport 30000:32767 -j DNAT --to-destination 10.0.2.4:30000-32767/30000
'''
DST_IP = "10.0.2.4"
DPORT = "30000:32767"

chain = iptc.Chain( iptc.Table(iptc.Table.NAT), "PREROUTING" )
rule = iptc.Rule()
rule.protocol = "tcp"
rule.dst = DST_IP # "10.0.2.4"
rule.match = rule.create_match( "tcp" )
rule.match.dport = DPORT # "30000:32767"
rule.target = rule.create_target( "DNAT" )
rule.target.to_destination = DST_IP + ":" + DPORT.replace(":", "-") # DST_IP + ":30000-32767/30000"

chain.insert_rule( rule )
'''


# sudo iptables -t nat -A POSTROUTING -p tcp --dport 30000:32767 -j SNAT --to-source 10.0.2.15
'''
SRC_IP = "10.0.2.15"
DPORT = "30000:32767"

chain = iptc.Chain( iptc.Table(iptc.Table.NAT), "POSTROUTING" )
rule = iptc.Rule()
rule.protocol = "tcp"
rule.match = rule.create_match( "tcp" )
rule.match.dport = DPORT # "30000:32767"
rule.target = rule.create_target( "SNAT" )
rule.target.to_source = SRC_IP

chain.insert_rule( rule )
'''


# sudo iptables -I INPUT -p tcp --dport 30000:32767 -j ACCEPT
'''
DPORT = "30000:32767"

chain = iptc.Chain( iptc.Table(iptc.Table.FILTER), "INPUT" )
rule = iptc.Rule()
rule.protocol = "tcp"
#rule.dst = ""
rule.match = rule.create_match( "tcp" )
rule.match.dport = DPORT # "30000:32767"
rule.target = rule.create_target( "ACCEPT" )

chain.insert_rule( rule )
'''


# sudo iptables -I FORWARD -j ACCEPT
'''
chain = iptc.Chain( iptc.Table(iptc.Table.FILTER), "FORWARD" )
rule = iptc.Rule()
rule.target = rule.create_target( "ACCEPT" )

chain.insert_rule( rule )
'''


# sudo iptables -I FORWARD -m state -p tcp --dport 30000:32767 --state NEW,RELATED,ESTABLISHED -j ACCEPT
'''
DPORT = "30000:32767"

chain = iptc.Chain( iptc.Table(iptc.Table.FILTER), "FORWARD" )
rule = iptc.Rule()
rule.protocol = "tcp"
#rule.dst = ""
match = rule.create_match( "tcp" )
match.dport = DPORT # "30000:32767"
rule.add_match( match )
match = rule.create_match( "state" )
match.state = "NEW,RELATED,ESTABLISHED"
rule.add_match( match )
rule.target = rule.create_target( "ACCEPT" )

chain.insert_rule( rule )
'''



# Server #2
# ----------------------------------------


'''
chain = iptc.Chain( iptc.Table(iptc.Table.FILTER), "FORWARD" )
rule = iptc.Rule()
rule.target = rule.create_target( "ACCEPT" )

chain.insert_rule( rule )
'''


# adds for new service

#sudo iptables -t nat -I PREROUTING -p tcp --dport 32579 -j DNAT --to-destination 10.0.2.5:32579
'''
DST_IP = "10.0.2.5"
DPORT = "32579"

chain = iptc.Chain( iptc.Table(iptc.Table.NAT), "PREROUTING" )
rule = iptc.Rule()
rule.protocol = "tcp"
rule.dst = DST_IP
rule.match = rule.create_match( "tcp" )
rule.match.dport = DPORT
rule.target = rule.create_target( "DNAT" )
rule.target.to_destination = DST_IP + ":" + DPORT

chain.insert_rule( rule )
'''

#sudo iptables -t nat -A POSTROUTING -p tcp --dport 32579 -j SNAT --to-source 10.0.2.4
'''
SRC_IP = "10.0.2.4"
DPORT = "32579"

chain = iptc.Chain( iptc.Table(iptc.Table.NAT), "POSTROUTING" )
rule = iptc.Rule()
rule.protocol = "tcp"
rule.match = rule.create_match( "tcp" )
rule.match.dport = DPORT
rule.target = rule.create_target( "SNAT" )
rule.target.to_source = SRC_IP

chain.insert_rule( rule )
'''

#sudo iptables -I INPUT -p tcp --dport 32579 -j ACCEPT
'''
DPORT = "32579"

chain = iptc.Chain( iptc.Table(iptc.Table.FILTER), "INPUT" )
rule = iptc.Rule()
rule.protocol = "tcp"
#rule.dst = ""
rule.match = rule.create_match( "tcp" )
rule.match.dport = DPORT
rule.target = rule.create_target( "ACCEPT" )

chain.insert_rule( rule )
'''

#sudo iptables -I FORWARD -m state -p tcp --dport 32579 --state NEW,RELATED,ESTABLISHED -j ACCEPT
'''
DPORT = "32579"

chain = iptc.Chain( iptc.Table(iptc.Table.FILTER), "FORWARD" )
rule = iptc.Rule()
rule.protocol = "tcp"
#rule.dst = ""
match = rule.create_match( "tcp" )
match.dport = DPORT
rule.add_match( match )
match = rule.create_match( "state" )
match.state = "NEW,RELATED,ESTABLISHED"
rule.add_match( match )
rule.target = rule.create_target( "ACCEPT" )

chain.insert_rule( rule )
'''



def add_rule(SRC_IP, DST_IP, DPORT, INIT = False):
    if INIT == True:
        # sudo iptables -I FORWARD -j ACCEPT
        '''
        chain = iptc.Chain( iptc.Table(iptc.Table.FILTER), "FORWARD" )
        rule = iptc.Rule()
        rule.target = rule.create_target( "ACCEPT" )

        chain.insert_rule( rule )
        '''

        # FIXME:
        # - find a rule: FORWARD ACCEPT ALL

    # -----

    #sudo iptables -t nat -I PREROUTING -p tcp --dport 32579 -j DNAT --to-destination 10.0.2.5:32579

    #DST_IP = "10.0.2.5"
    #DPORT = "32579"

    chain = iptc.Chain( iptc.Table(iptc.Table.NAT), "PREROUTING" )
    rule = iptc.Rule()
    rule.protocol = "tcp"
    rule.dst = DST_IP
    rule.match = rule.create_match( "tcp" )
    rule.match.dport = DPORT
    rule.target = rule.create_target( "DNAT" )
    if DPORT.find("-") > 0:
        rule.target.to_destination = DST_IP + ":" + DPORT.replace(":", "-") # DST_IP + ":30000-32767"
    else:
        rule.target.to_destination = DST_IP + ":" + DPORT

    chain.insert_rule( rule )

    # -----

    #sudo iptables -t nat -A POSTROUTING -p tcp --dport 32579 -j SNAT --to-source 10.0.2.4

    #SRC_IP = "10.0.2.4"
    #DPORT = "32579"

    chain = iptc.Chain( iptc.Table(iptc.Table.NAT), "POSTROUTING" )
    rule = iptc.Rule()
    rule.protocol = "tcp"
    rule.match = rule.create_match( "tcp" )
    rule.match.dport = DPORT
    rule.target = rule.create_target( "SNAT" )
    rule.target.to_source = SRC_IP

    chain.insert_rule( rule )

    # -----

    #sudo iptables -I INPUT -p tcp --dport 32579 -j ACCEPT

    #DPORT = "32579"

    chain = iptc.Chain( iptc.Table(iptc.Table.FILTER), "INPUT" )
    rule = iptc.Rule()
    rule.protocol = "tcp"
    rule.match = rule.create_match( "tcp" )
    rule.match.dport = DPORT
    rule.target = rule.create_target( "ACCEPT" )

    chain.insert_rule( rule )

    # -----

    #sudo iptables -I FORWARD -m state -p tcp --dport 32579 --state NEW,RELATED,ESTABLISHED -j ACCEPT

    #DPORT = "32579"

    chain = iptc.Chain( iptc.Table(iptc.Table.FILTER), "FORWARD" )
    rule = iptc.Rule()
    rule.protocol = "tcp"
    match = rule.create_match( "tcp" )
    match.dport = DPORT
    rule.add_match( match )
    match = rule.create_match( "state" )
    match.state = "NEW,RELATED,ESTABLISHED"
    rule.add_match( match )
    rule.target = rule.create_target( "ACCEPT" )

    chain.insert_rule( rule )

# TODO:
def delete_rule(DST_IP, DPORT):
    pass


if __name__ == "__main__":

    SRC_IP = "10.0.2.4"
    DST_IP = "10.0.2.5"
    DPORT = "32579"

    #add_rule( SRC_IP, DST_IP, DPORT )
    #delete_rule( DST_IP, DPORT )


