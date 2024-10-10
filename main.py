import pulp
from haversine import haversine, Unit
import folium

# Definição das coordenadas dos pontos (latitude, longitude)
points = {
    'SAAE1': (-22.056067, -47.906624),
    'SAAE2': (-22.029408, -47.874192),
    'SAAE3': (-22.022213, -47.897600),
    'SAAE4': (-22.009414, -47.892042),
    'SAAE5': (-22.005740, -47.873665),
    'SAAE6': (-22.007573, -47.889043),
    'SAAE7': (-22.006214, -47.899628),
    'SAAE8': (-21.989030, -47.917174),
    'Campus2': (-22.008774, -47.929795),
    'Campus1': (-22.008018, -47.896600),
    'UFSCar': (-21.983547, -47.880959)
}

# Função para calcular a distância entre dois pontos usando Haversine
def calculate_distances(points):
    distances = {}
    for i in points:
        for j in points:
            if i != j:
                distances[(i, j)] = haversine(points[i], points[j], unit=Unit.KILOMETERS)
    return distances

# Cálculo das distâncias entre todos os pontos
distances = calculate_distances(points)

# Criação do problema de programação linear
prob = pulp.LpProblem("Water_Distribution_Cost_Minimization", pulp.LpMinimize)

# Variáveis de decisão: fluxo de água entre os pontos (em milhares de litros)
flow_vars = pulp.LpVariable.dicts("Flow", distances.keys(), lowBound=0, cat='Continuous')

# Multiplicadores dos custos de acordo com o tipo de conexão
cost_multipliers = {
    ('SAAE', 'Campus'): 0.83,
    ('SAAE', 'SAAE'): 0.53,
    ('Campus', 'Campus'): 0.71
}

# Função para determinar o multiplicador correto com base no tipo de conexão
def get_cost_multiplier(i, j):
    if 'SAAE' in i and 'Campus' in j:
        return cost_multipliers[('SAAE', 'Campus')]
    elif 'SAAE' in i and 'SAAE' in j:
        return cost_multipliers[('SAAE', 'SAAE')]
    else:
        return cost_multipliers[('Campus', 'Campus')]

# Função objetivo: minimizar o custo total
prob += pulp.lpSum([flow_vars[(i, j)] * distances[(i, j)] * get_cost_multiplier(i, j) for (i, j) in distances]), "Total Cost"

# Suprimento/Demanda (milhares de litros)
supply_demand = {
    'SAAE1': 30, 'SAAE2': 40, 'SAAE3': 50, 'SAAE4': 30,
    'SAAE5': 50, 'SAAE6': 30, 'SAAE7': 30, 'SAAE8': 90,
    'Campus1': -120, 'Campus2': -100, 'UFSCar': -130
}

# Restrições de balanço de fluxo para cada ponto
for point in supply_demand:
    incoming = pulp.lpSum([flow_vars[(i, point)] for (i, j) in distances if j == point])
    outgoing = pulp.lpSum([flow_vars[(point, j)] for (i, j) in distances if i == point])
    
    # Restrição de fluxo: fluxo que entra - fluxo que sai = suprimento/demanda do ponto
    prob += (incoming - outgoing == supply_demand[point]), f"Flow_Balance_{point}"

# Resolver o problema
prob.solve()

# Exibir o status da solução
print("Status:", pulp.LpStatus[prob.status])

# Coordenadas centrais de São Carlos para o mapa
central_point = [-22.005740, -47.873665]

# Criar o mapa centrado em São Carlos
map_sao_carlos = folium.Map(location=central_point, zoom_start=13)

# Adicionar os pontos ao mapa
for point, coord in points.items():
    if 'Campus' in point or 'UFSCar' in point:
        # As universidades são marcadas com ícones vermelhos
        folium.Marker(location=coord, popup=point, tooltip=point, icon=folium.Icon(color='red')).add_to(map_sao_carlos)
    else:
        # As estações SAAE têm o ícone padrão
        folium.Marker(location=coord, popup=point, tooltip=point).add_to(map_sao_carlos)

# Adicionar TODAS as conexões possíveis como linhas pretas (caminhos possíveis)
for (i, j) in distances.keys():
    folium.PolyLine(
        locations=[points[i], points[j]],  # Coordenadas dos pontos conectados
        color='black',                     # Cor preta para conexões possíveis
        weight=1,                          # Espessura menor para as conexões sem fluxo
        opacity=0.5,
        popup=f"Conexão: {i} - {j}"
    ).add_to(map_sao_carlos)

# Adicionar as conexões (fluxos de água) com base nos fluxos calculados (linhas azuis)
for (i, j), flow_value in flow_vars.items():
    if flow_value.varValue > 0:  # Se houver fluxo entre os pontos
        distance = distances[(i, j)]
        cost_multiplier = get_cost_multiplier(i, j)
        unit_cost = distance * cost_multiplier
        total_cost = unit_cost * flow_value.varValue  # Custo total para o fluxo específico

        folium.PolyLine(
            locations=[points[i], points[j]],  # Coordenadas dos pontos conectados
            color='blue',                      # Cor da linha
            weight=2 + flow_value.varValue / 10,  # Espessura proporcional ao fluxo
            opacity=0.7,
            popup=(f"Fluxo: {flow_value.varValue} mil litros<br>"
                   f"Distância: {distance:.2f} km<br>"
                   f"Custo Unitário: R$ {unit_cost:.2f}/mil litros<br>"
                   f"Custo Total do Fluxo: R$ {total_cost:.2f}")
        ).add_to(map_sao_carlos)

# Salvar o mapa como arquivo HTML
map_sao_carlos.save("mapa_fluxo_agua.html")
