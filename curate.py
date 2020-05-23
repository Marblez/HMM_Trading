file1 = open('./raw/growthresults.txt', 'r') 
Lines = file1.readlines() 
arr = []
count = 0
# Strips the newline character 
for line in Lines: 
    text = line.strip()
    if len(text) < 51:
        arr.append(text + "\n")
    
file2 = open('./results/growth.txt', 'w') 
file2.writelines(arr) 
