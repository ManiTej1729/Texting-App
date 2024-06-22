#include <iostream>
#include <vector>
#include <map>

#define mod 1000000007

using namespace std;

int dfs(vector < vector <int> > &graph, int start, int currDepth, vector <bool> &visited) {
    visited[start] = true;
    int n = graph[start].size();
    int height = 0;
    int isEnd = 1;
    for (int i = 0; i < n; i++) {
        if (!visited[graph[start][i]]) {
            isEnd = 0;
            int temp = dfs(graph, graph[start][i], currDepth + 1, visited);
            if (temp > height) {
                height = temp;
            }
        }
    }
    if (isEnd == 1) {
        return currDepth;
    }
    return height;
}

int main() {

    for (int i = 0; i < 32; i++) {
        cout << (char) i << " ";
    }
    cout << "\n";

    return 0;
}
