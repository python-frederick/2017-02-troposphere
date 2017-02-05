### Packer and Troposphere

Run the troposphere script to see the current state.

> python packer-id-template.py old-ami-id

Update the files/test.txt and run the new build.

> packer build test.json 

Make note of the ami-id.

Run the updated tropospere script as follows.

> python packer-id-template.py ami-id
