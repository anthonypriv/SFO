# results validation

import matplotlib.pyplot as plt
from postgres import query_postgres


def terminal_subplot(ax, data, xname, ymax, zmax, terminal_code, color):
	# plot data for terminal
	term_data = [d for d in data if d['terminal'] == terminal_code]
	x = [d[xname] for d in term_data]
	y1 = [d['travel'] for d in term_data]
	z = [d['sample'] for d in term_data]

	# dwell = ax.bar(x, y0, color=color, alpha=.5, label='dwell time')
	travel = ax.bar(x, y1, color=color, label='travel time')
	ax.grid(axis='y', alpha=.5, linestyle='--')
	ax.set_title(terminal_code, fontsize=10, fontweight='bold')
	ax.set_xlabel(' '.join(xname.split('_')), fontsize=8, fontweight='bold')
	ax.set_ylabel('avg c2g (mins)', fontsize=8, fontweight='bold')
	ax.set_ylim(0, 1.1*ymax)
	ax.set_xticks(x)
	ax.xaxis.set_tick_params(labelsize=7)

	xy = zip(x, y1) if type(x[0]) is not str else enumerate(y1)
	for i, v in xy:
		ax.text(i-.12, v+3, int(v), color='k', fontsize=5)
	
	axp = ax.twinx()  # twin axis for sample size
	sample = axp.plot(x, z, color='k', label='sample')
	axp.set_ylim(0, 1.15*zmax)
	axp.set_ylabel('sample size', fontsize=8, fontweight='bold')

	alines, alabs = ax.get_legend_handles_labels()
	blines, blabs = axp.get_legend_handles_labels()
	axp.legend(alines+blines, alabs+blabs, prop={'size': 6}, loc=2)


def terminal_hist(env, repl, xname):
	sql = open('queries/curb_to_gate_agg.sql').read()
	query = sql.replace('___', repl)
	data = query_postgres(env, query)  # query data
	ymax = max([d['travel'] for d in data])

	# sample size fix (to account for gate propagation)
	if 'gate' not in xname:
		for d in data:
			d['sample'] /= term_gates[d['terminal']]
	zmax = max([d['sample'] for d in data])

	fig, (ax1, ax2, ax3, ax4, ax5) = plt.subplots(5, 1, figsize=(8, 11))
	terminal_subplot(ax1, data, xname, ymax, zmax, 'ITA', 'blue')
	terminal_subplot(ax2, data, xname, ymax, zmax, 'ITG', 'red')
	terminal_subplot(ax3, data, xname, ymax, zmax, 'T1', 'orange')
	terminal_subplot(ax4, data, xname, ymax, zmax, 'T2', 'purple')
	terminal_subplot(ax5, data, xname, ymax, zmax, 'T3', 'green')
	fig.suptitle('Time to Gate (by %s)' % ' '.join(xname.split('_')), fontsize=15, fontweight='bold')
	fig.tight_layout(rect=[0, 0, 1, .97])
	fig.savefig('figures/%s.png' % xname, dpi=300)


env = 'dev'
# gate_count = query_postgres(env, gate_count_sql)  # gates per terminal
# gates = {row['terminal_code']: int(row['count']) for row in gate_count}

gates_query = """
select gates.terminal_code as terminal, c2g.gate_id as gate
from curb_to_gate_matrix as c2g
left join vw_gate_ref as gates on gates.gate_id = c2g.gate_id
where c2g.batch_timestamp = (select max(batch_timestamp) from curb_to_gate_matrix)
group by gates.terminal_code, c2g.gate_id;
"""
gates = query_postgres(env, gates_query)
term_gates = {}
for gate in gates:
	if gate['terminal'] not in term_gates:
		term_gates[gate['terminal']] = 0
	term_gates[gate['terminal']] += 1

terminal_hist(env, 'doors.door_number', 'door_number')
terminal_hist(env, 'gates.gate_display_name', 'gate_display_name')
terminal_hist(env, 'c2g.day_of_week', 'day_of_week')
terminal_hist(env, 'c2g.hour_of_day', 'hour_of_day')
