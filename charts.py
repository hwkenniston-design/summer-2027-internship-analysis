import utils
import matplotlib.pyplot as plt

df = utils.load_all_snapshots()
print(len(df), "postings")

df.posted_month.value_counts().sort_index().plot(kind='bar')
plt.title('Summer 2027 data internships by month posted')
plt.ylabel('Postings')
plt.tight_layout()
plt.savefig('chart_by_month.png')
print("saved chart_by_month.png")

plt.figure()
df.accepts_bachelors.value_counts().plot(kind='bar')
plt.title("Summer 2027 data internships: accepts a bachelor's?")
plt.ylabel('Postings')
plt.tight_layout()
plt.savefig('chart_degrees.png')

plt.figure()
df.company_name.value_counts().head(10).plot(kind='barh')
plt.title('Top 10 companies posting data internships')
plt.xlabel('Postings')
plt.tight_layout()
plt.savefig('chart_companies.png')
print("saved all three")