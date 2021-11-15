# lambda-learning-csv
This is a fundamental test with lambda and s3 interaction

I have been trying to learn Lambda with some functional interaction to s3.

vpc_size = event['size'] driven from an event such as SNS. Derives the vpc constructs.

This is a work in progress project. 

3 Files are held in S3 
example-large.csv
example-medium.csv
example-small.csv

Row 2 contains an array of available CIDR spaces 
x.x.x.x/22 within the large csv
x.x.x.x/23 within the medium csv
x.x.x.x/24 within the small csv 

The main objective is a simple idea of obtaining IP data, albeit I havent tested the reverse .

It uses basic iteration to read from a list, the remove the entry so on next read is the next on the list etc.

You need to update the py file with the S3 bucket name you have, and also allow lambda the permissions for interaction

Also note endpoints are created here so ensure you destroy if not required
