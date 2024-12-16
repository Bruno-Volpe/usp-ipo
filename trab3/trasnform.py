def parse_adjacency_matrix(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    # Find the start of the adjacency matrix
    start_index = lines.index('Adjacency Matrix:\n') + 1
    end_index = lines.index('Positions:\n')

    # Extract the matrix
    matrix = []
    for line in lines[start_index:end_index]:
        row = list(map(int, line.strip().split()))
        matrix.append(row)

    return matrix

# Example usage
file_path = './problem_1.txt'
adjacency_matrix = parse_adjacency_matrix(file_path)

# Display the adjacency matrix
for row in adjacency_matrix:
    print(row)
