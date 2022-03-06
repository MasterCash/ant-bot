

def getClusters(maxX = 600, maxY = 600) -> tuple[list[tuple[int, int]], list[tuple[int,int]]]:
  points: set[tuple[int, int]] = set()
  cluster: list[tuple[int, int]] = []

  for y in range(maxY + 1):
    for x in range(maxX + 1):
      points.add((x, y))
      if(x % 3 == 0 and y % 4 == 0 and y < maxY - maxY % 4 and x < maxX - maxX % 3):
        cluster.append((x, y))

  for point in cluster:
    for loc in [(point[0] + x, point[1] + x + 1) for x in range(4)]:
      if loc in points:
        points.remove(loc)
    for loc in [(point[0] + x, point[1] + x) for x in range(5)]:
      if loc in points:
        points.remove(loc)
    for loc in [(point[0] + x, point[1] + x - 1) for x in range(1,5)]:
      if loc in points:
        points.remove(loc)
  print(f"{len(cluster)} clusters")
  print(f"{len(points)} missed points")
  return (cluster, list(points))

if __name__ == "__main__":
  getClusters()