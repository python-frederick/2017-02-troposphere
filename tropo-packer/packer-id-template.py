#!/usr/bin/python

from troposphere import Base64, FindInMap, GetAtt, Join, Output
from troposphere import Parameter, Ref, Tags, Template
from troposphere.autoscaling import Metadata
from troposphere.ec2 import PortRange, NetworkAcl, Route, \
    VPCGatewayAttachment, SubnetRouteTableAssociation, Subnet, RouteTable, \
    VPC, NetworkInterfaceProperty, NetworkAclEntry, \
    SubnetNetworkAclAssociation, EIP, Instance, InternetGateway, \
    SecurityGroupRule, SecurityGroup
from troposphere.policies import CreationPolicy, ResourceSignal
from troposphere.cloudformation import Init, InitFile, InitFiles, \
    InitConfig, InitService, InitServices
import boto3
import sys
import datetime

ami_id = sys.argv[1]
stack_name = 'testing%s' % datetime.datetime.now().strftime("%Y%M%d%H%M")

t = Template()

t.add_version('2010-09-09')

t.add_description("""Test template to take in new ami id from packer""")

keyname_param = t.add_parameter(
    Parameter(
        'KeyName',
        ConstraintDescription='must be the name of an existing EC2 KeyPair.',
        Description='Name of an existing EC2 KeyPair to enable SSH access to \
the instance',
        Type='AWS::EC2::KeyPair::KeyName',
        Default='keyname'
    ))

amiid_param = t.add_parameter(
    Parameter(
        'AMIID',
        ConstraintDescription='AMI ID of the new image',
        Description='AMI ID of the new image',
        Type='String',
        Default=ami_id
    ))


sshlocation_param = t.add_parameter(
    Parameter(
        'SSHLocation',
        Description=' The IP address range that can be used to SSH to the EC2 \
instances',
        Type='String',
        MinLength='9',
        MaxLength='18',
        Default='0.0.0.0/0',
        AllowedPattern="(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})/(\d{1,2})",
        ConstraintDescription=(
            "must be a valid IP CIDR range of the form x.x.x.x/x."),
    ))

instanceType_param = t.add_parameter(Parameter(
    'InstanceType',
    Type='String',
    Description='WebServer EC2 instance type',
    Default='t2.micro',
    AllowedValues=[
        't2.micro', 't2.small', 't2.medium',
        'm2.xlarge', 'm2.2xlarge', 'm2.4xlarge',
        'm3.medium', 'm3.large', 'm3.xlarge', 'm3.2xlarge'
    ],
    ConstraintDescription='must be a valid EC2 instance type.',
))


t.add_mapping('AWSInstanceType2Arch', {
    't2.micro': {'Arch': 'HVM64'},
    't2.small': {'Arch': 'HVM64'},
    't2.medium': {'Arch': 'HVM64'},
    'm3.medium': {'Arch': 'HVM64'},
    'm3.large': {'Arch': 'HVM64'},
    'm3.xlarge': {'Arch': 'HVM64'},
    'm3.2xlarge': {'Arch': 'HVM64'},
})

ref_stack_id = Ref('AWS::StackId')
ref_region = Ref('AWS::Region')
ref_stack_name = Ref('AWS::StackName')

VPC = t.add_resource(
    VPC(
        'VPC',
        CidrBlock='10.0.0.0/16',
        Tags=Tags(
            Application=ref_stack_id)))

subnet = t.add_resource(
    Subnet(
        'Subnet',
        CidrBlock='10.0.0.0/24',
        VpcId=Ref(VPC),
        Tags=Tags(
            Application=ref_stack_id)))

internetGateway = t.add_resource(
    InternetGateway(
        'InternetGateway',
        Tags=Tags(
            Application=ref_stack_id)))

gatewayAttachment = t.add_resource(
    VPCGatewayAttachment(
        'AttachGateway',
        VpcId=Ref(VPC),
        InternetGatewayId=Ref(internetGateway)))

routeTable = t.add_resource(
    RouteTable(
        'RouteTable',
        VpcId=Ref(VPC),
        Tags=Tags(
            Application=ref_stack_id)))

route = t.add_resource(
    Route(
        'Route',
        DependsOn='AttachGateway',
        GatewayId=Ref('InternetGateway'),
        DestinationCidrBlock='0.0.0.0/0',
        RouteTableId=Ref(routeTable),
    ))

subnetRouteTableAssociation = t.add_resource(
    SubnetRouteTableAssociation(
        'SubnetRouteTableAssociation',
        SubnetId=Ref(subnet),
        RouteTableId=Ref(routeTable),
    ))

networkAcl = t.add_resource(
    NetworkAcl(
        'NetworkAcl',
        VpcId=Ref(VPC),
        Tags=Tags(
            Application=ref_stack_id),
    ))

inBoundPrivateNetworkAclEntry = t.add_resource(
    NetworkAclEntry(
        'InboundHTTPNetworkAclEntry',
        NetworkAclId=Ref(networkAcl),
        RuleNumber='100',
        Protocol='6',
        PortRange=PortRange(To='80', From='80'),
        Egress='false',
        RuleAction='allow',
        CidrBlock='0.0.0.0/0',
    ))

inboundSSHNetworkAclEntry = t.add_resource(
    NetworkAclEntry(
        'InboundSSHNetworkAclEntry',
        NetworkAclId=Ref(networkAcl),
        RuleNumber='101',
        Protocol='6',
        PortRange=PortRange(To='22', From='22'),
        Egress='false',
        RuleAction='allow',
        CidrBlock='0.0.0.0/0',
    ))

inboundResponsePortsNetworkAclEntry = t.add_resource(
    NetworkAclEntry(
        'InboundResponsePortsNetworkAclEntry',
        NetworkAclId=Ref(networkAcl),
        RuleNumber='102',
        Protocol='6',
        PortRange=PortRange(To='65535', From='1024'),
        Egress='false',
        RuleAction='allow',
        CidrBlock='0.0.0.0/0',
    ))

outBoundHTTPNetworkAclEntry = t.add_resource(
    NetworkAclEntry(
        'OutBoundHTTPNetworkAclEntry',
        NetworkAclId=Ref(networkAcl),
        RuleNumber='100',
        Protocol='6',
        PortRange=PortRange(To='80', From='80'),
        Egress='true',
        RuleAction='allow',
        CidrBlock='0.0.0.0/0',
    ))

outBoundHTTPSNetworkAclEntry = t.add_resource(
    NetworkAclEntry(
        'OutBoundHTTPSNetworkAclEntry',
        NetworkAclId=Ref(networkAcl),
        RuleNumber='101',
        Protocol='6',
        PortRange=PortRange(To='443', From='443'),
        Egress='true',
        RuleAction='allow',
        CidrBlock='0.0.0.0/0',
    ))

outBoundResponsePortsNetworkAclEntry = t.add_resource(
    NetworkAclEntry(
        'OutBoundResponsePortsNetworkAclEntry',
        NetworkAclId=Ref(networkAcl),
        RuleNumber='102',
        Protocol='6',
        PortRange=PortRange(To='65535', From='1024'),
        Egress='true',
        RuleAction='allow',
        CidrBlock='0.0.0.0/0',
    ))

subnetNetworkAclAssociation = t.add_resource(
    SubnetNetworkAclAssociation(
        'SubnetNetworkAclAssociation',
        SubnetId=Ref(subnet),
        NetworkAclId=Ref(networkAcl),
    ))

instanceSecurityGroup = t.add_resource(
    SecurityGroup(
        'InstanceSecurityGroup',
        GroupDescription='Enable SSH access via port 22',
        SecurityGroupIngress=[
            SecurityGroupRule(
                IpProtocol='tcp',
                FromPort='22',
                ToPort='22',
                CidrIp=Ref(sshlocation_param)),
            SecurityGroupRule(
                IpProtocol='tcp',
                FromPort='80',
                ToPort='80',
                CidrIp='0.0.0.0/0')],
        VpcId=Ref(VPC),
    ))

instance_metadata = Metadata(
    Init({
        'config': InitConfig(
            packages={'yum': {'httpd': []}},
            commands={
                'copytest': {'command': 'cp /home/ec2-user/test.txt /var/www/html/'}
                },
            files=InitFiles({
                '/etc/cfn/cfn-hup.conf': InitFile(content=Join('',
                                                               ['[main]\n',
                                                                'stack=',
                                                                ref_stack_id,
                                                                '\n',
                                                                'region=',
                                                                ref_region,
                                                                '\n',
                                                                ]),
                                                  mode='000400',
                                                  owner='root',
                                                  group='root'),
                '/etc/cfn/hooks.d/cfn-auto-reloader.conf': InitFile(
                    content=Join('',
                                 ['[cfn-auto-reloader-hook]\n',
                                  'triggers=post.update\n',
                                  'path=Resources.WebServerInstance.\
Metadata.AWS::CloudFormation::Init\n',
                                  'action=/opt/aws/bin/cfn-init -v ',
                                  '         --stack ',
                                  ref_stack_name,
                                  '         --resource WebServerInstance ',
                                  '         --region ',
                                  ref_region,
                                  '\n',
                                  'runas=root\n',
                                  ]))}),
            services={
                'sysvinit': InitServices({
                    'httpd': InitService(
                        enabled=True,
                                         ensureRunning=True),
                    'cfn-hup': InitService(
                        enabled=True,
                        ensureRunning=True,
                        files=[
                            '/etc/cfn/cfn-hup.conf',
                            '/etc/cfn/hooks.d/cfn-auto-reloader.conf'
                        ])})})}))

instance = t.add_resource(
    Instance(
        'WebServerInstance',
        Metadata=instance_metadata,
        ImageId=Ref(amiid_param),
        InstanceType=Ref(instanceType_param),
        KeyName=Ref(keyname_param),
        NetworkInterfaces=[
            NetworkInterfaceProperty(
                GroupSet=[
                    Ref(instanceSecurityGroup)],
                AssociatePublicIpAddress='true',
                DeviceIndex='0',
                DeleteOnTermination='true',
                SubnetId=Ref(subnet))],
        UserData=Base64(
            Join(
                '',
                [
                    '#!/bin/bash -xe\n',
                    'yum update -y aws-cfn-bootstrap\n',
                    '/opt/aws/bin/cfn-init -v ',
                    '         --stack ',
                    Ref('AWS::StackName'),
                    '         --resource WebServerInstance ',
                    '         --region ',
                    Ref('AWS::Region'),
                    '\n',
                    '/opt/aws/bin/cfn-signal -e $? ',
                    '         --stack ',
                    Ref('AWS::StackName'),
                    '         --resource WebServerInstance ',
                    '         --region ',
                    Ref('AWS::Region'),
                    '\n',
                ])),
        CreationPolicy=CreationPolicy(
            ResourceSignal=ResourceSignal(
                Timeout='PT15M')),
        Tags=Tags(
            Application=ref_stack_id),
    ))

ipAddress = t.add_resource(
    EIP('IPAddress',
        DependsOn='AttachGateway',
        Domain='vpc',
        InstanceId=Ref(instance)
        ))

t.add_output(
    [Output('URL',
            Description='Newly created application URL',
            Value=Join('',
                       ['http://',
                        GetAtt('WebServerInstance',
                               'PublicIp'), '/test.txt']))])

#print(t.to_json())

client = boto3.client('cloudformation')

response = client.create_stack(
    StackName=stack_name,
    TemplateBody=t.to_json(),
    #Parameters=[
    #    {
    #        'ParameterKey': 'string',
    #        'ParameterValue': 'string',
    #        'UsePreviousValue': True|False
    #    },
    #],
    DisableRollback=True
    #TimeoutInMinutes=123,
    #Capabilities=[
    #    'CAPABILITY_IAM'|'CAPABILITY_NAMED_IAM',
    #],
    #ResourceTypes=[
    #    'string',
    #],
    #OnFailure='DO_NOTHING'
    #StackPolicyBody='string',
    #StackPolicyURL='string',
)

print(response)
