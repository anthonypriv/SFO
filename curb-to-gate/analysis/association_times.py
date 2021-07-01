# association times

from postgres import query_postgres
import matplotlib.pyplot as plt


def plot_association_times(query_name):
	data = query_postgres('dev', query_name)
	x = [d['event_timestamp'] for d in data]
	y = [d['count'] for d in data]

	plt.figure()
	plt.bar([i for i, _ in enumerate(x)], y)
	plt.show()


def plot_session_len(query_name):
	data = query_postgres('dev', query_name)
	x = [d['session_len'] for d in data]
	y = [d['count'] for d in data]

	plt.figure(figsize=(35,5))
	plt.grid(axis='y', alpha=.5, linestyle='--', linewidth=.5)
	plt.bar(x, y)
	plt.xticks(range(0, int(max(x)), 100))
	plt.yticks(range(0, int(max(y)), 250))
	plt.xlim(0, max(x))
	plt.ylim(0, 3000)
	plt.xlabel('Session Length (seconds)')
	plt.ylabel('Count')
	plt.title('Session Length Frequency', fontsize=17)
	plt.tight_layout()
	plt.savefig('figures/session_len.png', dpi=350)


def term_session_plot(ax, data, terminal, color, xmax):
	x = [d['session_len'] for d in data if d['terminal'] == terminal]
	y = [d['count'] for d in data if d['terminal'] == terminal]

	ax.grid(axis='y', alpha=.5, linestyle='--', linewidth=.5)
	ax.bar(x, y, color=color)
	ax.set_title(terminal, fontsize=12, fontweight='bold')
	ax.set_xlim(0, xmax)
	# ax.set_ylim(0, 3000)
	ax.set_xticks(range(0, xmax, 100))
	# ax.set_yticks(range(0, int(max(y)), 250))
	ax.set_xlabel('session length (seconds)')
	ax.set_ylabel('count')


def terminal_session_len(query_name):
	data = query_postgres('dev', query_name)
	xmax = int(max([d['session_len'] for d in data]))
	fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(35, 15))
	term_session_plot(ax1, data, 'ITB', 'blue', xmax)
	term_session_plot(ax2, data, 'T1', 'orange', xmax)
	term_session_plot(ax3, data, 'T2', 'purple', xmax)
	term_session_plot(ax4, data, 'T3', 'green', xmax)
	fig.suptitle('Session Length by Terminal', fontsize=20, fontweight='bold')
	fig.tight_layout(rect=[0, 0, 1, .97])
	fig.savefig('figures/%s.png' % query_name, dpi=350)


# plot_association_times('association_times')
# plot_session_len('session_len')
terminal_session_len('terminal_session_len')
