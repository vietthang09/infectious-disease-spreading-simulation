**Infectious Disease Spreading Simulation**

Implement a population-based simulation using a cellular finite state automaton on a 2D grid   
(periodic boundaries). Each cell contains at most one **agent** (except the school environment in subtask 4). Agents move randomly to a neighbouring cell (or stay) each time step. There are four states:

\- **Healthy (H)** – susceptible, not immune.  
\- **Infected (I)** – newly infected, not yet infectious (incubation period lasts **N** days/steps).  
\- **Sick (S)** – infectious (can transmit the disease, not necessarily show all those days symptoms).  
\- **Recovered (R)** – after being Sick, an agent either becomes immune (probability **s**) or dies   
  (probability **d**), with **s \+ d \= 1**. Dead agents are removed from the grid (empty cell).

**Parameters** (each to be varied in experiments):

\- **p** – infection risk per contact (when a Healthy agent is adjacent to a Sick agent).  
\- **N** – incubation period (days/steps between Infection and becoming Sick).  
\- **s, d**  – recovery immunity and death probabilities (from Sick state).  
\- movement radius **R** – for subtask 3, limit how far an agent can move from its initial location (e.g., 0 \= no movement, 1 \= adjacent, 2 \= up to two steps etc).  
\- **pmask** – reduced infection risk when prevention measures (masks) are used.  
\- school parameters – for subtask 4: **X** \= number of agents in the school room, **p’** \= increased  
   infection risk inside school, plus a daily schedule.  
\- **Initial condition**: one agent is “patient zero” in the Infected state (day 0 of incubation). All others are Healthy.

**Simulation output**:  
\- Visual animation of agent states (color-coded) at each time step.  
\- Macroscopic summary: number of agents in each state over time (line plots).

**Four Subtasks (approximately equal in depth and required work)**

**Subtask 1**: Parameter exploration – what makes a disease extremely dangerous?

\- Implement the basic model (without movement restrictions, prevention, or school).

\- Choose at least three different parameter sets (e.g., low/high **p**, short/long N, various **s/d** combinations). Run each for a fixed number of steps (e.g., 200\) and record the final fraction of the population that is dead, recovered, and still sick.

\- **Determine a parameter set that makes the disease “extremely dangerous**” – define your own metric (e.g., highest death toll, longest epidemic duration, largest peak of simultaneously sick agents). Compare the epidemic curves (number of Infected+Sick over time) for the different sets.

\- Deliverable: graphs of epidemic curves for each parameter set, a table of final outcomes, and a written justification for your “extremely dangerous” parameter set.

**Subtask 2:** Influence of death rate **d** and immunity **s** on disease wave length

\- Fix all parameters except **d** and **s** (with **s \= 1 − d**). Choose a moderate baseline (e.g., **p \= 0.3, N \= 5**).

\- Run simulations for a range of **d** values (e.g., 0.0, 0.1, 0.2, …, 0.9). For each value, record the duration of the epidemic (time steps until no Sick or Infected remain) and the total death count.

\- Discuss: How does the length of the disease wave change when \*d\* increases? When \*s\* increases? Is there a non‑monotonic relationship? Provide explanations based on the dynamics (e.g., higher death removes infectious individuals but also reduces herd immunity).

\- Deliverable: plots of epidemic duration vs. **d** and total deaths vs. \*d\*, plus a short discussion (≈150 words).

**Subtask 3:** Movement restrictions and prevention measures (masks, social distancing)

\- Extend the model with two new features:

  \- Limited movement radius – each agent can move at most **R** cells away from its initial location. (Euclidean or Manhattan distance). 

  \- Prevention measures – when masks are used, the infection risk is reduced from **p** to **p\_mask** (e.g., p\_mask \= p/2). Social distancing can be modelled as reducing the probability that two agents become adjacent (or reducing movement).

**Design experiments to answer:**

  \- How does limiting movement to R \= 0 (isolated agents) affect the peak number of Sick agents compared to free movement ?

  \- How does wearing masks change the total number of infections over the whole simulation?

  \- Combine both measures: what is the synergistic effect?

\- Deliverable: comparative graphs (e.g., time series of Sick agents for different **R** and **p\_mask** values) and a short report on the effectiveness of each measure.

**Subtask 4:** Outbreak in an environment with a school

\- Add a school schedule to the simulation. The grid contains a designated “school room” (a small cluster of cells, e.g., 5×5, where every cell can host more than one agent). 

\- Hour‑wise clock: each time step represents one hour. From 9:00 to 15:00 (6 hours), a fixed set of **X** agents (e.g., 30 out of the total population) are forced to occupy the school room. They move only within that room (tight location). Outside school hours, they move normally.

\- Inside the school, the infection risk is increased to **p’** (e.g., **p’ \= 2×p** or higher). All other rules remain.

\- **Experiments**:

  \- Run the simulation with and without the school (same total population and initial conditions). Compare the epidemic curves.

  \- Vary **X** (number of students) and **p’** (school infection risk). How do these parameters influence the timing and size of the infection peak?

  \- Discuss how a school outbreak can “seed” the wider population.

\- Deliverable: at least two graphs showing differences (e.g., Sick count over time with/without school) and a discussion (≈150 words) of public health implications (e.g., effectiveness of school closures).

**General Requirements for All Subtasks**

* For each subtask, run at least 5 simulation repetitions (with different random seeds) and report averages as well as standard deviations.  
* Provide clear figures with labelled axes and legends.  
* Include the commented source code (or pseudocode) of your simulation.  
* Write a single report with four clearly separated sections (one per subtask), each of approximately equal length (target: 3-6pages  per subtask including figures).

**Evaluation criteria:** correctness of implementation, clarity of experiments, depth of analysis, and quality of visualisations.