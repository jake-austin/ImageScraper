"""
This is a file that helps control iterations in the scraper itself

We define here a Loop_Controller which controls the iteration and
recursion within the scraper.

These controllers will define the kwargs of all controllers in recursive calls

They must be iterators that return tuples of (kwargs (dict or None),
"""


class Controller():
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __iter__(self):
        raise NotImplementedError

    def __next__(self):
        raise NotImplementedError

    def __len__(self):
        raise NotImplementedError


class DefaultController(Controller):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.depth = kwargs['depth']
        self.original_number = kwargs['original_number']
        self.original_depth = kwargs['original_depth']
        self.scaling_factor = kwargs['scaling_factor']
        self.iterlength = int(self.original_number / ((self.original_depth - self.original_depth + 1)))

    def __len__(self):
        return self.iterlength

    def __iter__(self):
        self.n = 0
        self.new_depth = self.depth
        return self

    def __next__(self):
        """
        must either raise stopiteration error if done, return None if no recursion is to be done, or return
        the kwargs dictionary for the recursive controller
        :return:
        """
        if self.n > self.iterlength:
            raise StopIteration
        self.n+=1
        if self.new_depth > 1:
            # decrement depth by an amount so when we've reached (num images looked on this function call) /
            # scaling_factor number of images, depth == 1
            self.new_depth -= ((self.original_depth - 1) / int(
                self.original_number / (self.original_depth - self.depth + 1))) * self.scaling_factor
            return {'depth': self.new_depth - 1,
                    'original_number': self.original_number,
                    'original_depth': self.original_depth,
                    'scaling_factor': self.scaling_factor}
        return None
