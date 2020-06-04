from troposphere.ec2 import VPC,NetworkAclEntry,PortRange

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
Tags,
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

"""GIT Variables"""

GithubAccount = "jadoxo"
GithubAnsibleURL = "https://github.com/{}/ansible".format(GithubAccount)

"""  [MODIFIED Jenkins]   Define variables"""

ApplicationName = "Jenkins"
ApplicationPort = "8080"
t = Template()


"""Ansible Pull command"""
AnsiblePullCmd = "/usr/local/bin/ansible-pull -U {} {}.yml -i localhost".format(
	GithubAnsibleURL,
	ApplicationName
)

"""Ansible /User Data : configure to get it from ansible"""

ud = Base64(Join('\n', [
	"#!/bin/bash",
	"yum install --enablerepo=epel -y git",
	"pip install ansible",
	AnsiblePullCmd,
	"echo '*/10 * * * * {}' > /etc/cron.d/ansiblepull".format(AnsiblePullCmd)
]))

"""[MODIFIED Jenkins] Add Role to Jenkins server"""
t.add_resource(Role(
	'trorol',
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
	'InstanceProfile',
	Path="/",
	Roles=[Ref('trorol')]
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

t.add_resource(VPC(
	'trovpc',
	EnableDnsSupport=True,
	EnableDnsHostnames=True,
	CidrBlock='172.31.0.0/16',
))
"""Subnet : Creation"""

t.add_resource(ec2.Subnet(
	'trosub',
	CidrBlock='192.168.100.0/24',
	VpcId=Ref('trovpc'),
))
"""I-GW : creation"""

t.add_resource(ec2.InternetGateway(
	'trointgat',
))
"""VpcGatewayAttachment"""

t.add_resource(ec2.VPCGatewayAttachment(
	'trovpcgatatt',
	VpcId=Ref('trovpc'),
	InternetGatewayId=Ref('trointgat'),
))
"""Route Table : creation"""

t.add_resource(ec2.RouteTable(
	'troroutab',
	VpcId=Ref('trovpc'),
))
"""Route : creation"""

t.add_resource(ec2.Route(
	'trorou',
	DestinationCidrBlock='0.0.0.0/0',
	GatewayId=Ref('trointgat'),
	DependsOn=Ref('trovpcintgatatt'),
	RouteTableId=Ref('troroutab'),
	
))
"""Subnet & Route Table association"""

t.add_resource(ec2.SubnetRouteTableAssociation(
	'trosubroutabass',
	SubnetId=Ref('trosub'),
	RouteTableId=Ref('routab'),
))
"""Network ACL CREATION"""

t.add_resource(ec2.NetworkAcl(
	'tronetacl',
	VpcId=Ref('trovpc'),
))
""" Network ACL ENTRY 1 """

t.add_resource(ec2.NetworkAclEntry(
	'tronetaclent1',
	NetworkAclId=Ref('tronetacl'),
	RuleNumber='100',
	RuleAction='allow',
	Protocol='-1',
	CidrBlock='0.0.0.0/0',
	PortRange=PortRange(To="80", From="80"),
	Egress=False,
))
""" Network ACL ENTRY 2 """

t.add_resource(ec2.NetworkAclEntry(
        'tronetaclent2',
        NetworkAclId=Ref('tronetacl'),
        RuleNumber='200',
        RuleAction='Deny',
        Protocol='6',
        CidrBlock='0.0.0.0/0',
        PortRange=PortRange(To="22",From="22"),
        Egress='false',
))

"""Security Group creation"""

t.add_resource(ec2.SecurityGroup(
	'trosecgro',
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


"""UserData value

ud = Base64(Join('\n', [
"#!/bin/bash",
"sudo yum install --enablerepo=epel -y nodejs",
"wget http://bit.ly/2vESNuc -O /home/ec2-user/helloworld.js",
"wget http://bit.ly/2vVvT18 -O /etc/init/helloworld.conf",
"start helloworld"
]))
"""

"""[Modified jenkins] EC2 Resource creation Creation"""

t.add_resource(
	ec2.Instance(
		'troins',
		InstanceType='t2.micro',
		SecurityGroups=[Ref('trosecgro')],
		ImageId='ami-a4c7edb2',
		KeyName=Ref('keypair'),
		UserData=ud,
		IamInstanceProfile=Ref('InstanceProfile'),
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
