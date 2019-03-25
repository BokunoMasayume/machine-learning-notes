
# coding: utf-8

# # 导入jupyter notebook 作为模块
# 
# 有一个很大众的问题就是人们希望从Jupyter Notebooks导入代码。因为Notebooks不是平常的Python文件，所以这有点困难---它不能被标准Python组织导入。
# 
# 
# 幸运的是，Python在导入组织中提供了非常精巧的“钩子”`(hooks)`，因此我们可以只使用公共API，轻松的导入Jupyter Notebooks。

# >ps: `!jupyter nbconvert mnist_loader.ipynb --to slides --post serve`
# 用来生成ppt...点阵图，非常低清orz

# In[1]:


import io, os, sys, types


# In[2]:


from IPython import get_ipython
from nbformat import read
from IPython.core.interactiveshell import InteractiveShell


# 导入钩子通常以两个对象的形式：
#     1. 一个模块加载器（**Module Loader**），拿取一个模块名字，比如IPython.display，然后返回一个模块
#     2. 一个模块寻找器（**Module Finder**），搞清楚一个模块是否存在，然后告诉Python用哪个**Loader**

# In[3]:


def find_notebook(fullname ,path=None):
    """
    找到已知名字和可选路径的Notebook
    
    把"foo.bar"变成"foo/bar.ipynb"
    如果"Foo_Bar"不存在，会试着把"Foo_Bar"变成"Foo Bar"
    """
    name = fullname.rsplit('.',1)[-1]
    if not path:
        path=['']
    
    for d in path:
        nb_path = os.path.join(d,name+".ipynb")
        if os.path.isfile(nb_path):
            return nb_path
        nb_path = nb_path.replace("_"," ")
        if os.path.isfile(nb_path):
            return nb_path


# ## 笔记加载器
# 在这里我们有我们的Noteboook Loader。它很简单--只要我们弄清楚了模块的文件名，它要做的只是：
#     1. 把笔记文档加载到内存
#     2. 创建一个空的模块
#     3. 执行模块命名空间的每个单元格
#     
# 因为IPython 单元格可以有扩展语法，IPython变换用来在执行之前把这些单元格的每一个变成他们的纯Pyton副本。如果你的Notebook单元格就是纯Python的，那这步就没必要了。
# 

# In[4]:


class NotebookLoader(object):
    def __init__(self,path=None):
        self.shell = InteractiveShell.instance()
        self.path = path
        
    def load_module(self,fullname):
        path = find_notebook(fullname,self.path)
        
        print("importing Jupyter notebook from %s" % path)
        
        with io.open(path,'r',encoding='utf-8') as f:
            nb = read(f,4)
            
        
        #创建模块，并把它加入 sys.modules
        #如果 name 在 sys.modules:
        #    return sys.modules[name]
        mod = types.ModuleType(fullname)
        mod.__file__ = path
        mod.__loader__  = self
        mod.__dict__['get_ipython'] = get_ipython
        sys.modules[fullname] = mod
        
        #额外的工作确保对 user_ns 有影响
        #确实影响到 notebook module's ns
        save_user_ns = self.shell.user_ns
        self.shell.user_ns = mod.__dict__
        
        try:
            for cell in nb.cells:
                if cell.cell_type == 'code':
                    code = self.shell.input_transformer_manager.transform_cell(cell.source)
                    exec(code , mod.__dict__)
        finally:
            self.shell.user_ns = save_user_ns
        return mod


# ## 模块寻找器
# 寻找器是个简单的对象，它告诉你一个name 能否被import ，并返回相应的加载器。它做的事就是当你
# ```
# import mynotebook
# ```
# 时做检查。它检查 mynotebook.ipynb 是否存在。如果找着了，返回一个笔记加载器。
# 
# 一个额外的逻辑是用来解决packages里的路径

# In[7]:


class NotebookFinder(object):
    def __init__(self):
        self.loaders={}
        
    def find_module(self,fullname,path=None):
        nb_path = find_notebook(fullname,path)
        if not nb_path:
            return
        key = path
        if path:
            key = os.path.sep.join(path)
            
        if key not in self.loaders:
            self.loaders[key] = NotebookLoader(path)
        return self.loaders[key]


# ## 注册钩子
# 

# In[8]:


sys.meta_path.append(NotebookFinder())

