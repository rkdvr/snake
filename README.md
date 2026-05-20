# Snake Game

Snake is one of the most iconic video games in history, popularized in the late 1990s when Nokia pre-installed it on its mobile phones. The player controls a growing snake that moves across a grid, eating food to grow longer — but must avoid hitting the walls or its own body. Simple in concept, endlessly replayable in practice, it became one of the first games millions of people ever played. 

What makes Snake a compelling programming project is how naturally it maps to core Python concepts. The snake itself is just a list of coordinates. Movement is adding a new head and removing the tail. Collision is a membership check. Every mechanic in the game is a fundamental data structure problem in disguise, making it an ideal project for learning how code and logic translate into something you can actually play.  
## Requirements
- Python 3.13
- pygame

## Setup
1. Clone the repo:
   git clone <your-repo-url>
   cd snake

2. Create and activate the environment:
   ```conda env create -f environment.yaml
   conda activate snake_environment```

3. Run the game:
   python src/snake_basic.py
   python src/snake_intermediate.py
   python src/snake_advanced.py

## Project Structure
```
snake/
├── src/                  
│   ├── snake_basic.py
│   ├── snake_intermediate.py
│   └── snake_advanced.py
├── tests/                
│   └── test_snake_basic.py
├── .gitignore
├── environment.yml
├── requirements.txt
└── README.md
```

## Authors
- Lois Celorico
- Erika De Vera
- Naiza Glorioso
- Reinhard Mozo
