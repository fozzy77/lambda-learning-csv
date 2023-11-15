## Import libraries which complete execution
import boto3
import botocore
from ipaddress import ip_network
from itertools import cycle
import json
import os
import csv
from pprint import pprint
from tempfile import NamedTemporaryFile

unique_bucket = os.environ['unique_bucket']


## Invoke the boto3 ec2 clinet for AWS related calls

ec2 = boto3.client("ec2")
s3 = boto3.client("s3")

## Define the lambda handler using the standard default name

def lambda_handler(event, context):
    print("The Whole message event")
    print(event)
    
    ### variable to be sourced from event
    messages = event['Records']
    print("The Records dictionary from the whole message")
    print(messages)
    for message in messages :
        messageData = {
        'body': message['body']
        }
    print("The Element we have focused on for a variable input")
    print(messageData)
    vpc_size = messageData['body']
 
 
    azs = ["eu-west-2a", "eu-west-2b", "eu-west-2c"]
    
    if vpc_size == "small":
        subnet_size = 27
        number_of_subnets_to_use = 6
        subnet_csv = 'example-small.csv'
    elif vpc_size == "medium":
        subnet_size = 26
        number_of_subnets_to_use = 9
        subnet_csv = 'example-medium.csv'
    elif vpc_size == "large":
        subnet_size = 25
        number_of_subnets_to_use = 9
        subnet_csv = 'example-large.csv'
    else:
        print("Incorrect VPC size defined")
        exit(1)

    obj = s3.get_object(Bucket=unique_bucket, Key=subnet_csv)
    print(obj)
    content = obj['Body'].read().decode('utf-8')
    print(content)
    
    s3.download_file(unique_bucket, subnet_csv, '/tmp/tmp-example.csv')
    list_dir = os.listdir('/tmp')
    print("List of tmp directory")
    print(list_dir)
    
    cidr_space =[]

    with open('/tmp/tmp-example.csv', newline='', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        i = 0
        for row in csv_reader:
            if i == 0:
                index, network_supernet, allocated, b, c, d, e = row
                print("Index 0 row cidr supernet with conditional loop to cidr_space")
                print(str(network_supernet))
                cidr_space.append(network_supernet)
            i +=1

    
    print("selected cidr_space extracted and stripped for consumption") 
    stripped_cidr = str(cidr_space).strip("[']")
    print(stripped_cidr)
    
    with open('/tmp/tmp-example.csv', newline='', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader)
        with open('/tmp/tmp-update.csv', 'w') as new_file:
            csv_writer = csv.writer(new_file, delimiter=',')
            for line in csv_reader:
                csv_writer.writerow(line)
            print("Load in CSV omit first 1 rows then recommit to S3")
            print(csv_writer)
        

    s3.upload_file('/tmp/tmp-update.csv', unique_bucket, subnet_csv )

### variable to be set by call to IPAM solution
    supernet = stripped_cidr
    
    all_subnets_in_supernet = list(ip_network(supernet).subnets(new_prefix=subnet_size))
    
    allocated_subnets = list(
        zip(all_subnets_in_supernet[:number_of_subnets_to_use], cycle(azs))
    )
    
    for subnet, region in allocated_subnets:
        print(f"cidr: {subnet} for region: {region}")
        cidr = str(subnet)
        print(type(cidr))
        print(cidr)
    
    print(
        f"\nremaining unallocated subnets from {supernet}: {all_subnets_in_supernet[number_of_subnets_to_use:]}"
    )

### Creation of VPC Data

    response = ec2.create_vpc(CidrBlock=supernet)
    print(response)
    
    vpcid = response["Vpc"]["VpcId"]
    waiter = ec2.get_waiter('vpc_available')
    waiter.wait(
        Filters=[
            {
                'Name': 'state',
                'Values': [
                    'available',
                ]
            },
        ],
        VpcIds=[vpcid
        ],
        WaiterConfig={
            'Delay' : 1,
            'MaxAttempts': 20
        }
        )
    print(waiter.wait)

### Creation of Subnets and building a subnetidlist with Subnet id references

    subnetidlist=[]
    for subnet, region in allocated_subnets:
        print(f"cidr: {subnet} for region: {region}")
        cidr = str(subnet)
        net = ec2.create_subnet(
            AvailabilityZone=region,
            CidrBlock=cidr,
            VpcId=vpcid,
            )
        print(cidr)
        subid = net["Subnet"]["SubnetId"]
        subnetidlist.append(subid)   

    print(subnetidlist)
    print(
        f"\nremaining unallocated subnets from {supernet}: {all_subnets_in_supernet[number_of_subnets_to_use:]}"
    )

### Create NACL and moving subnets into the particular NACL entry

    networkACL = ec2.create_network_acl( VpcId = vpcid )
    print(networkACL)
    networkACL_id = networkACL["NetworkAcl"]["NetworkAclId"]
    print (networkACL_id)

### Create NACL rule entries for the above invoked networkACL id 

    networkACL_entry  = ec2.create_network_acl_entry(
    CidrBlock='10.0.0.0/8',
    Egress=False,
    NetworkAclId=networkACL_id,
    PortRange={
        'From': 53,
        'To': 53
    },
    Protocol='17',
    RuleAction='allow',
    RuleNumber=100
)
    networkACL_entry  = ec2.create_network_acl_entry(
    CidrBlock='10.0.0.0/8',
    Egress=False,
    NetworkAclId=networkACL_id,
    PortRange={
        'From': 22,
        'To': 22
    },
    Protocol='6',
    RuleAction='allow',
    RuleNumber=110
)
    networkACL_entry  = ec2.create_network_acl_entry(
    CidrBlock='10.0.0.0/8',
    Egress=False,
    NetworkAclId=networkACL_id,
    PortRange={
        'From': 443,
        'To': 443
    },
    Protocol='6',
    RuleAction='allow',
    RuleNumber=120
)
    networkACL_entry  = ec2.create_network_acl_entry(
    CidrBlock='10.0.0.0/8',
    Egress=True,
    NetworkAclId=networkACL_id,
    PortRange={
        'From': 1024,
        'To': 65525
    },
    Protocol='6',
    RuleAction='allow',
    RuleNumber=120
)

### Get default ACL from Account

    acl_response = ec2.describe_network_acls( NetworkAclIds=[], Filters=[] )
  
### List the associations by NetworkAclId

    for acl in acl_response['NetworkAcls']:
        for association in acl['Associations']:
            print(association['NetworkAclId'])
            id = (association['NetworkAclId'])

### Get association IDs for ofermentioned NetworkAcls, build a list with criteria

    myAssociations = []
    for acl in acl_response['NetworkAcls']:
        if( acl["VpcId"] == vpcid and len( acl['Associations'] ) > 0 ):
            myAssociations = acl['Associations']
            print(myAssociations)
            break

### Replace associations from default nacl based on the criteria to the new ACL

    for a in myAssociations:
         ec2.replace_network_acl_association(
             AssociationId = a['NetworkAclAssociationId'],
             NetworkAclId = networkACL['NetworkAcl']['NetworkAclId']
    )

### Attach subnets to a non-default routing table 

    privaterttable = ec2.create_route_table(
    DryRun=False,
    VpcId=vpcid
    )
    privaterttableid = privaterttable['RouteTable']['RouteTableId']
    
### Creating a standard route table
    
    j = 0
    for id in range(len(subnetidlist)):
        route_table_association = ec2.associate_route_table(
            SubnetId=subnetidlist[j],
            RouteTableId=privaterttableid)
        j += 1
        
### Looping through subnetidlist and associating subnets to routing table     
  
    security_group = ec2.create_security_group(
    Description='default-sg',
    GroupName='default-sg',
    VpcId=vpcid
    )
    print(security_group)

### Adding a default Security Group

 #   s3_gate_endpoint = ec2.create_vpc_endpoint(
 #   VpcEndpointType='Gateway',
 #   VpcId=vpcid,
 #   ServiceName='com.amazonaws.eu-west-2.s3',
 #   RouteTableIds=[
 #       privaterttableid,
 #   PrivateDnsEnabled=False,
 #   ],
 #   )
 #   print(s3_gate_endpoint)

### Adding Local S3 endpoint### Adding Local S3 endpoint
