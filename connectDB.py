import pyodbc

# data koneksi sql server

# ganti disini
SERVER = 'LAPTOP-PVCB9MBF\SQLEXPRESS'
DATABASE = 'tubesJarkom'
USERNAME = 'sa'
PASSWORD = 'jOuter2407123#*'

connectionString = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};Trusted_Connection=yes;TrustServerCertificate=yes;'

# buat koneksi ke sql server
conn = pyodbc.connect(connectionString)