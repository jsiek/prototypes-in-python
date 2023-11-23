from abstract_syntax import *

def check_proof(proof, env):
  match proof:
    case PTrue(loc):
      return Bool(True)

def check_proof_of(proof, formula, env):
  form = check_proof(proof, env)
  if not equal(form, formula):
    raise Exception('expected proof of ' + str(formula) + ' not ' + str(form))
      
