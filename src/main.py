from game import Game
from replay import Replay
from notation import generate_fen
from pieces import Side
from config import AUTO_PROMO

def main():    
    game = Game()
    replay = None
    
    while True:
        print(game.board)
        
        jogada = None        
        lado = 'brancas' if game.status.side == Side.WHITE else 'pretas'
        print(f"\nJogam as {lado}")
                
        while True:
            entrada = input("lance (ou 'fen', 'replay', 'sair'): ").strip()
            if entrada in ('sair', 'replay'):
                break

            if entrada == 'fen':
                print(generate_fen(game.board.grid, game.status)+"\n")
                continue
                          
            jogada = entrada.split()
            if len(jogada) != 2:
                print("Erro: informe origem e destino, ex: 'e2 e4'\n")
                continue
            
            if jogada is not None:
                try:
                    if not AUTO_PROMO and game.will_promote(*jogada):
                        options = "Q R B N" if game.status.side == Side.WHITE else "q r b n"
                        promotion = input(f"escolha a peça a promover ({options}): ")                        
                        game.play(*jogada, promotion)
                    else:
                        game.play(*jogada)
                        
                    print()
                    break
                except ValueError as erro:
                    print(f"Erro: {erro}\n") 
                    
        if game.status.finished:
            print(game.board)
            
            if game.status.check_mate is not None:
                vencedor = 'brancas' if game.status.check_mate == Side.WHITE else 'pretas'
                print(f"\nXeque-Mate! Vitória das {vencedor}")
            
            elif game.status.draw is not None:
                print(f"\nEmpate! {game.status.draw.value}")
               
            entrada = input("\nDigite 'replay' ou 'sair': ").strip()

        elif entrada not in ('sair', 'replay'):
            continue

        if entrada == 'replay':
            replay = Replay(game)

        break

    if replay is not None:
        print(replay)
        while True:
            entrada = input("\nDigite '<', '>', '<<' '>>' ou 'sair': ").strip()
            
            if entrada == 'sair':
                break
            
            match(entrada):
                case '<':
                    replay.back()
                case '>':
                    replay.next()
                case '<<':
                    replay.first()
                case '>>':
                    replay.last()
                case _:
                    print("Entrada inválida!")
                    continue

            print(replay)


if __name__ == "__main__":
    main()
