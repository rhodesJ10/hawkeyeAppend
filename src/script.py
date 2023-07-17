from utils import readDocuments
from model import Game


def main():
    data = readDocuments()

    game = Game()
    game.transformData(data)
    game.createJson()


if __name__ == "__main__":
    main()