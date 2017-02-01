from troposphere import Template, Output, Ref, Parameter
import troposphere.ec2 as ec2
t = Template()

# Instance names in list
instance_names = ['instance1', 'instance2', 'instance3', 'instance4']

image_id = t.add_parameter(Parameter(
    "imageid",
    Description="AMI ID for instance",
    Type="String",
))

instance_size = t.add_parameter(Parameter(
    "InstanceSize",
    Description="Set the instance size",
    Type="String",
))

for instance_name in instance_names:
    instance = ec2.Instance(instance_name)
    instance.ImageId = Ref(image_id)
    instance.InstanceType = Ref(instance_size)
    t.add_resource(instance)
    t.add_output([
        Output(
            "Instanceid%s" % instance_name,
            Description="InstanceId of the newly created EC2 instance",
            Value=Ref(instance),
        )])

print(t.to_json())


