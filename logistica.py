def definir_transporte(quantidade_missionarios, com_mala=True):
    if quantidade_missionarios == 0 or str(quantidade_missionarios) == 'nan':
        return ""
    
    # Capacidades da linha: Missionários com mala
    if com_mala:
        if quantidade_missionarios <= 1: return "1 CARRO"
        elif quantidade_missionarios <= 4: return "1 VAN"
        elif quantidade_missionarios <= 6: return "1 VAN MICRO"
        elif quantidade_missionarios <= 18: return "1 MICRO"
        elif quantidade_missionarios <= 25: return "1 ÔNIBUS"
        else: return "1 ÔNIBUS + 1 FURGÃO (MALAS)"
        
    # Capacidades da linha: Missionários sem mala
    else:
        if quantidade_missionarios <= 4: return "1 CARRO"
        elif quantidade_missionarios <= 15: return "1 VAN"
        elif quantidade_missionarios <= 18: return "1 VAN MICRO"
        elif quantidade_missionarios <= 30: return "1 MICRO"
        elif quantidade_missionarios <= 46: return "1 ÔNIBUS"
        else: return "2 ÔNIBUS"

        