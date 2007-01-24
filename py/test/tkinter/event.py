
class Event:
   def __init__(self, *args, **kwargs):
      self.args = args
      self.kwargs = kwargs
      self.callbacks = []

      
   def __call__(self, *args, **kwargs):
      default_kwargs = kwargs.copy()
      default_kwargs.update(kwargs)
      for callable in self.callbacks:
         callable(*args, **default_kwargs)

   def subscribe(self, callable):
      self.callbacks.append(callable)

   def remove(self, callable):
      while f in self.callbacks: self.callbacks.remove(f)
