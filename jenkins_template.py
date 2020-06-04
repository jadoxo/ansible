"""Import Template tools"""
from troposphere import (
Base64,
GetAtt,
Join,
Ref,
)

"""Import Cloudformation stack components """
from troposphere import (
Output,
Parameter,
Template,
)

"""Import AWS services"""
from troposphere import (
ec2,
)

"""[MODIFIED Jenkins] Import :  AWAC & tropossphere:IAM"""
from troposphere.iam import (
InstanceProfile,
PolicyType as IAMPolicy,
Role,
)
from awacs.aws import (
Action,
Allow,
Policy,
Principal,
Statement,
)
from awacs.sts import AssumeRole

"""  [MODIFIED Jenkins]   Define variables"""
GithubAccount = "jadoxo"
GithubAnsibleURL = "https://github.com/{}/ansible".format(GithubAccount)
ApplicationName = "Jenkins"
ApplicationPort = "8080"
t = Template()

"""[MODIFIED Jenkins] Add Role to Jenkins server"""
t.add_resource(Role(
	"Role",
	AssumeRolePolicyDocument=Policy(
		Statement=[
			Statement(
				Effect=Allow,
				Action=[AssumeRole],
				Principal=Principal("Service", ["ec2.amazonaws.com"])
			)
		]
	)
))

"""[Modified Jenkins] Add a role to Jenkins server"""
t.add_resource(InstanceProfile(
	"InstanceProfile",
	Path="/",
	Roles=[Ref("Role")]
))

"""Template description"""
t.add_description("Effective DevOps in AWS: HelloWorld web application")


"""Parameter Creation"""
t.add_parameter(Parameter(
	'keypair',
	Description='KeyPair parameter',
	Type='AWS::EC2::KeyPair::KeyName',
	ConstraintDescription='must be the name of an existing EC2 KeyPair',
))

""" VPC : creation"""
t.add_resource(ec2.Vpc(
	'tro_vpc',
	EnableDnsSupport=True,
	EnableDnsHostname=True,
	CidrBlock='192.168.0.0/16',
	Tags=Tags(
		Stack_Name=Ref('AWS::StackName'),
		Stack_ID=Ref('AWS::StackId'),
		Stack_Region=Ref('AWS::Region'),
	)
))

"""Subnet : Creation"""
t.add_resource(ec2.Subnet(
	'tro_sub',
	CidrBlock='192.168.100.0/24',
	VpcId=Ref(tropo_vpc),
	Tags=Tags(
                Stack_Name=Ref('AWS::StackName'),
                Stack_ID=Ref('AWS::StackId'),
                Stack_Region=Ref('AWS::Region'),
        )
)

"""I-GW : creation"""
t.add_resource(ec2.InternetGateway(
	'tro_int_gat',
	Tags=Tags(
                Stack_Name=Ref('AWS::StackName'),
                Stack_ID=Ref('AWS::StackId'),
                Stack_Region=Ref('AWS::Region'),
        )
))


"""VpcGatewayAttachment"""
t.add_resource(ec2.VpcGatewayAttachment(
	'tro_vpc_gat_att',
	VpcIp=Ref(Tropo Internet Gateway),
	GatewayId=Ref(tro_int_gat),
	Tags=Tags(
                Stack_Name=Ref('AWS::StackName'),
                Stack_ID=Ref('AWS::StackId'),
                Stack_Region=Ref('AWS::Region'),
        )
))
"""Route Table : creation"""
t.add_resource(ec2.RouteTable(
	'tro_rou_tab',
	VpcId=Ref(tro_vpc),
	Tags=Tags(
                Stack_Name=Ref('AWS::StackName'),
                Stack_ID=Ref('AWS::StackId'),
                Stack_Region=Ref('AWS::Region'),
        )
))

"""Route : creation"""
t.add_resource(ec2.Route(
	'tro_rou',
	DestinationCidrBlock='0.0.0.0/0',
	GatewayId=Ref(tro_int_gat),
	DependsOn=Ref(tro_vpc_int_gat_att),
	RouteTableId=Ref(tro_rou_tab),
	
))

"""Subnet & Route Table association"""
t.add_resource(ec2.SubnetRouteTableAssociation(
	'tro_sub_rou_tab_ass',
	SubnetId=Ref(tro_sub),
	RouteTableId=Ref(rou_tab),
	Tags=Tags(
                Stack_Name=Ref('AWS::StackName'),
                Stack_ID=Ref('AWS::StackId'),
                Stack_Region=Ref('AWS::Region'),
        )
))

"""Network ACL CREATION"""
t.add_resource(ec2.NetworkAcl(
	'tro_net_acl',
	VpcId=Ref(tro_vpc),
	Tags=Tags(
                Stack_Name=Ref('AWS::StackName'),
                Stack_ID=Ref('AWS::StackId'),
                Stack_Region=Ref('AWS::Region'),
        )
))

""" Network ACL ENTRY 1 """
t.add_resource(ec2.NetworkAclEntry(
	'tro_net_acl_ent_1',
	NetworkAclId=Ref(tro_net_acl),
	RuleNumber='100',
	RuleAction='allow',
	Protocol='-1',
	CidrBlock='0.0.0.0/0',
	PortRange=PortRange(To='80',From='80'),
	Egress=False,
	
        )
))


""" Network ACL ENTRY 2 """
t.add_resource(ec2.NetworkAclEntry(
        'tro_net_acl_ent_1',
        NetworkAclId=Ref(tro_net_acl),
        RuleNumber='200',
        RuleAction='Deny',
        Protocol='6',
        CidrBlock='0.0.0.0/0',
        PortRange=PortRange(To='22',From='22'),
        Egress=False,
))



"""Security Group creation"""
t.add_resource(ec2.SecurityGroup(
	"TropoSecuritygroup",
	Tags=Tags(
                Stack_Name=Ref('AWS::StackName'),
                Stack_ID=Ref('AWS::StackId'),
                Stack_Region=Ref('AWS::Region'),
        )
	GroupDescription="Allow SSH and TCP/{} access".format(ApplicationPort),
	SecurityGroupIngress=[
		ec2.SecurityGroupRule(
		IpProtocol='tcp',
		FromPort='22',
		ToPort='22',
		CidrIp='0.0.0.0',
		),
		ec2.SecurityGroupRule(
		IpProtocol='tcp',
		FromPort=ApplicationPort,
		ToPort=ApplicationPort,
		CidrIp='0.0.0.0',
		),
	],

))


"""UserData value"""

ud = Base64(Join('\n', [
"#!/bin/bash",
"sudo yum install --enablerepo=epel -y nodejs",
"wget http://bit.ly/2vESNuc -O /home/ec2-user/helloworld.js",
"wget http://bit.ly/2vVvT18 -O /etc/init/helloworld.conf",
"start helloworld"
]))

"""[Modified jenkins] EC2 Resource creation Creation"""

t.add_resource(
	ec2.Instance(
		'tro_ins',
		InstanceType='t2.micro',
		SecurityGroups=[Ref('TropoSecuritygroup')],
		ImageId='ami-a4c7edb2',
		KeyName=Ref('keypair'),
		UserData=ud,
		IamInstanceProfile=Ref('InstanceProfile')
	)
))

t.add_output(
	Output(
		"myOutputPublicIP",
		Value=GetAtt("instance", "PublicIp"),
	)
),

t.add_output(
	Output(
		"PublicIPAddress",
		Value=GetAtt("instance", "PublicDnsName"),
	)
),
print t.to_json()
