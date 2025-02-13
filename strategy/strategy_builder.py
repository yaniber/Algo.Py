
class StrategyBaseClass():

    def __init__(self) -> None:
        '''
        Child class must initialize the strategy parameters here.
        '''
        pass

    def run(self):
        '''
        Function must return : entries, exits, close_data, open_data
        '''
        raise NotImplementedError()