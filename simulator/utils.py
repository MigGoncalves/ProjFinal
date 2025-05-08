import math

def calcular_resultados(y0, y1, r, rho, c0):
    s = y0 - c0
    c1 = (1 + r) * s + y1
    U0 = math.log(c0) + (1 / (1 + rho)) * math.log(c1)

    renda_total = y0 + y1 / (1 + r)
    c0_opt = (1 + rho) / (2 + rho) * renda_total
    c1_opt = (1 + r) / (2 + rho) * renda_total
    U0_max = math.log(c0_opt) + (1 / (1 + rho)) * math.log(c1_opt)

    percentagem = (U0 / U0_max) * 100
    return c1, s, U0, U0_max, percentagem

def calcular_consumo_utilidade(A, investimento, alpha, delta, r):
    # Consumo no período 1
     # Capital acumulado com o investimento
    K = investimento / delta

    # Valor presente com esse capital
    V0 = ((1 + r) / r) * (A * K**alpha - delta * K)

    # Capital ótimo
    K_opt = ((alpha * A) / (r + delta))**(1 / (1 - alpha))

    # Valor presente ótimo
    V0_max = ((1 + r) / r) * (A * K_opt**alpha - delta * K_opt)

    percentagem = (V0 / V0_max) * 100

    return K, V0, K_opt, V0_max, percentagem