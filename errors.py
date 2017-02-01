import troposphere.ec2 as ec2

# Incorrect property being set on AWS resource
instance = ec2.Instance("ec2instance", image="i-XXXX")

# Incorrect type for AWS resource property
#instance = ec2.Instance("ec2instance", ImageId=1)

# uncomment and comment line above run when ready
#instance = ec2.Instance("ec2instance", ImageId="ami-sadljf3")

from troposphere import Template
t = Template()
t.add_resource(instance)
print(t.to_json())