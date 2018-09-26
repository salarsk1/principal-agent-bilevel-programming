from agent import *
import pyipopt
import pickle
class Principal(object):

	def __init__(self, agent):

		self.agent = agent

		# if hasattr(self.agent, 'grad_VQ_compiled'):
		# 	pass
		# else:
		# self.agent()


	def neg_se_obj(self, param, e, g_x, others):

		self.sse_eff, self.sse_obj, self.g_p_obj, self.g_p_x = self.agent.solve_sse_opt_prob(param, others)

		tot_transfer = self.agent.tr_exp_compiled(self.sse_eff, param, *others)
		
		tot_val = self.agent.sysval_exp_compiled(self.sse_eff, others[0], others[1][:,0].reshape(-1, 1), others[2])
		
		return np.array(tot_transfer - tot_val).flatten()[0]

	def jac_neg_se_obj(self, param, e, g_x, others):

		weights = others[0]
		quads   = others[1][:,0]
		w_acc   = others[2]

		arr1 = np.ndarray(shape = (self.agent.ncoloc, 1))
		arr2 = np.ndarray(shape = (self.agent.ncoloc, self.agent.M))
		arr3 = np.ndarray(shape = (self.agent.ncoloc, 1))

		for i in range(self.agent.ncoloc):
			
			arr1[i, :] = self.agent.grad_trQ_compiled(np.array(e).flatten(), \
				param, np.array([[quads[i]]*self.agent.M]))[0][0]

			arr2[i, :] = self.agent.grad_tra_compiled(np.array(e).flatten(), \
				param, np.array([quads[i]]*self.agent.M).reshape(1,-1))

			arr3[i, :] = self.agent.grad_VQ_compiled(np.array(e).flatten(), \
				np.array([[quads[i]]]))[0][0]

		exp_trQ = np.dot(weights, arr1) / w_acc
		exp_tra = np.dot(weights, arr2) / w_acc
		exp_VQ  = np.dot(weights, arr3) / w_acc

		self.se_obj_jacobian = exp_tra - (exp_VQ - exp_trQ) * g_x * self.agent.kappa 

		return np.array(self.se_obj_jacobian).flatten()

	def optimize_contract(self, others, restarts = 10):
		
		N = self.agent.N
		M = self.agent.M

		result_dic                 = {}
		result_dic['se_obj']       = np.array([0.0])
		result_dic['parameters']   = np.array([0.0]*M)
		result_dic['sse_utility']  = np.array([0.0])
		result_dic['sse_effort']   = np.array([0.0])
		result_dic['sse_transfer'] = np.array([0.0])
		result_dic['sys_quality']  = np.array([0.0])


		nvar = M

		bnds = ([(1.0e-6, .7)]*nvar)

		a0 = np.random.uniform(1.0e-6, 0.7, nvar)

		self.sse_eff, self.sse_obj, self.g_p_obj, self.g_p_x = self.agent.solve_sse_opt_prob(a0, others)

		compare = np.infty
		result = None

		cons =  [{'type': 'ineq', 'fun': lambda x: -self.neg_se_obj(x, self.sse_eff, self.g_p_x, others), 
				'jac':lambda x: -self.jac_neg_se_obj(x, self.sse_eff, self.g_p_x, others)}]


		for r in restarts:
			print r
			res = opt.minimize(self.neg_se_obj, x0 = a0, args=(self.sse_eff, self.g_p_x, others), method = 'slsqp', 
								jac =  self.jac_neg_se_obj, constraints = cons, 
								options={'ftol':1.0e-6, 'maxiter':100, 'disp':False}, bounds = bnds)

			a0 = np.random.uniform(1.0e-6, 0.7, nvar)

			if res.fun < compare and res.status == 0 and res.success == True:
				compare = res.fun
				result = res
				agent_eff, agent_obj, agent_g_p_obj, agent_g_p_x = self.agent.solve_sse_opt_prob(result.x, others)

		result_dic['se_obj'] = np.array(-result.fun).flatten()
		result_dic['parameters'] = result.x
		result_dic['sse_utility'] = agent_obj
		result_dic['sse_effort'] = agent_eff
		result_dic['sse_transfer'] = self.agent.tr_exp_compiled(agent_eff, res.x, *others)
		result_dic['sys_quality']  = np.array(np.mean(self.agent.Q_compiled(agent_eff, others[1]), axis = 0)[0]).flatten()

		return result_dic
	


if __name__ == '__main__':
	from mpi4py	import MPI
	number_opt = 8
	comm = MPI.COMM_WORLD
	rank = comm.rank
	size = comm.size
	print rank
	print size
	if rank == 0:
		N                     = 1
		kappa                 = np.array([1.3])
		delta                 = np.array([0.2])
		cs                    = np.array([0.5])
		M                     = 6
		ncoloc                = 1000
		mu                    = np.linspace(0.5, 1.3, M)
		qvals                 = np.array([1.0])
		quads, weights, w_acc = roots_hermitenorm(ncoloc, mu=True)
		quads_bcast           = np.array([quads]*M).T
		weights               = weights.reshape(1, -1)
		others                = [weights, quads_bcast, w_acc]

		subsys = Agent(N, kappa, delta, cs, M, mu, qvals, ncoloc)
		subsys()
		sys = Principal(subsys)


		jobs = list(range(number_opt))
		jobs = split(jobs, size)

	else:
		N           = None
		kappa       = None
		delta       = None
		cs          = None
		M           = None
		ncoloc      = None
		mu          = None
		qvals       = None
		quads       = None
		weights     = None
		w_acc       = None
		quads_bcast = None
		others      = None
		sys         = None
		jobs        = None

	results_all = []
	jobs = comm.scatter(jobs, root=0)

	N = comm.bcast(N, root = 0)
	kappa = comm.bcast(kappa, root = 0)
	delta = comm.bcast(delta, root = 0)
	cs = comm.bcast(cs, root = 0)
	M = comm.bcast(M, root = 0)
	ncoloc = comm.bcast(ncoloc, root = 0)
	mu = comm.bcast(mu, root = 0)
	qvals = comm.bcast(qvals, root = 0)
	quads = comm.bcast(quads, root = 0)
	weights = comm.bcast(weights, root = 0)
	w_acc = comm.bcast(w_acc, root = 0)
	quads_bcast = comm.bcast(quads_bcast, root = 0)
	others = comm.bcast(others, root = 0)
	sys = comm.bcast(sys, root = 0)
	results_all = [sys.optimize_contract(others, restarts = jobs)]
	results_all = comm.gather(results_all, root = 0)

	if rank == 0:
		final_result = results_all[np.argmax([results_all[i][0]['se_obj'] for i in range(size)])]
		with open('test.pickle', 'wb') as myfile:
			pickle.dump((results_all, final_result), myfile)







