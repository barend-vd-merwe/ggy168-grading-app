library(torch)
options(scipen = 999)
rnd_error <- 1.0 * (10^(-4))
ang_error <- 1.5
dist_error <- 1.5
cmp_error <- 2.0

## gibbs free energy of reaction
## reagents
gp1 <- torch_tensor(-1582.0, requires_grad = TRUE)
mp1 <- torch_tensor(2.0, requires_grad = TRUE)
gp2 <- torch_tensor(-604.0, requires_grad=TRUE)
mp2 <- torch_tensor(1.0, requires_grad = TRUE)

gr1 <- torch_tensor(-1330.5, requires_grad = TRUE)
mr1 <- torch_tensor(2.0, requires_grad = TRUE)
gr2 <- torch_tensor(-237.1, requires_grad = TRUE)
mr2 <- torch_tensor(3.0, requires_grad = TRUE)
gr3 <- torch_tensor(-394.4, requires_grad = TRUE)
mr3 <- torch_tensor(1.0, requires_grad = TRUE)

## Product side

n1 <- gp1 * mp1
n1$retain_grad()

n2 <- gp2 * mp2
n2$retain_grad()

n6 <- n1 + n2
n6$retain_grad()

## Reagent side
n3 <- gr1 * mr1
n3$retain_grad()

n4 <- gr2 * mr2
n4$retain_grad()

n5 <- gr3 * mr3
n5$retain_grad()

n7 <- n3 + n4
n7$retain_grad()

n8 <- n7 + n5
n8$retain_grad()

## Answer
Y <- n6 - n8

Y$backward()

results <- data.frame(nodes = c("n1", "n2", "n3", "n4",
                                "n5", "n6", "n7", "n8", "Y"),
                      fwd = c(as.numeric(n1),
                              as.numeric(n2),
                              as.numeric(n3),
                              as.numeric(n4),
                              as.numeric(n5),
                              as.numeric(n6),
                              as.numeric(n7),
                              as.numeric(n8),
                              as.numeric(Y)),
                      part = c(abs(as.numeric(n1$grad)),
                               abs(as.numeric(n2$grad)),
                               abs(as.numeric(n3$grad)),
                               abs(as.numeric(n4$grad)),
                               abs(as.numeric(n5$grad)),
                               abs(as.numeric(n6$grad)),
                               abs(as.numeric(n7$grad)),
                               abs(as.numeric(n8$grad)),
                               1.0),
                      error = rep(rnd_error,9))

fc <- results$error %*% results$part
pc <- 2 * fc
Y
fc
pc

## Calculating phi size

d <- torch_tensor(0.125, requires_grad = TRUE)
c2 <- torch_tensor(2.0, requires_grad = TRUE)
cn1 <- torch_tensor(-1.0, requires_grad = TRUE)

n1 <- log10(d)
n1$retain_grad()

n2 <- log10(c2)
n2$retain_grad()

n3 <- n1 / n2
n3$retain_grad()

Y <- n3 * cn1

## backward pass
Y$backward()

results <- data.frame(nodes = c("n1", "n2", "n3", "Y"),
                      fwd = c(as.numeric(n1),
                              as.numeric(n2),
                              as.numeric(n3),
                              as.numeric(Y)),
                      part = c(abs(as.numeric(n1$grad)),
                               abs(as.numeric(n2$grad)),
                               abs(as.numeric(n3$grad)),
                               1.0),
                      error = rep(rnd_error, 4))

fc <- results$part %*% results$error
pc <- 2 * fc
Y
fc
pc

## penetration resistance (new method)

cg <- torch_tensor(9.8, requires_grad = TRUE)
h_weight <- torch_tensor(8.0, requires_grad = TRUE)
drop_dist_mm <- torch_tensor(575.0, requires_grad = TRUE)
pen_dist_cm <- torch_tensor(3.2, requires_grad = TRUE)
c1000 <- torch_tensor(1000.0, requires_grad = TRUE)
c100 <- torch_tensor(100.0, requires_grad = TRUE)
c2 <- torch_tensor(2.0, requires_grad = TRUE)

n1 <- drop_dist_mm / c1000
n1$retain_grad()

n2 <- pen_dist_cm / c100
n2$retain_grad()

n3 <- h_weight * cg
n3$retain_grad()

n4 <- n3 * n1
n4$retain_grad()

Y <- n4 / n2

## backward pass
Y$backward()

results <- data.frame(nodes = c("n1","n2","n3","n4","Y"),
                      fwd = c(as.numeric(n1),
                              as.numeric(n2),
                              as.numeric(n3),
                              as.numeric(n4),
                              as.numeric(Y)),
                      part = c(abs(as.numeric(n1$grad)),
                               abs(as.numeric(n2$grad)),
                               abs(as.numeric(n3$grad)),
                               abs(as.numeric(n4$grad)),
                               1.0),
                      error = rep(rnd_error, 5))

fc <- results$error %*% results$part
pc <- 2*fc

Y
fc
pc

## old method
n1 <- drop_dist_mm / c1000
n1$retain_grad()

n2 <- pen_dist_cm / c100
n2$retain_grad()

n3 <- cg * n1
n3$retain_grad()

n4 <- n3 * 2
n4$retain_grad()

n5 <- n4 * h_weight
n5$retain_grad()

n6 <- n5 / c2
n6$retain_grad()

Y <- n6 / n2

## backward
Y$backward()

results <- data.frame(nodes = c("n1","n2","n3","n4","n5","n6","Y"),
                      fwd = c(as.numeric(n1),
                              as.numeric(n2),
                              as.numeric(n3),
                              as.numeric(n4),
                              as.numeric(n5),
                              as.numeric(n6),
                              as.numeric(Y)),
                      part = c(abs(as.numeric(n1$grad)),
                               abs(as.numeric(n2$grad)),
                               abs(as.numeric(n3$grad)),
                               abs(as.numeric(n4$grad)),
                               abs(as.numeric(n5$grad)),
                               abs(as.numeric(n6$grad)),
                               1.0),
                      error = rep(rnd_error, 7))

fc <- results$part %*% results$error
pc <- 2*fc

Y
fc
pc

## Moisture content
dry <- torch_tensor(16.0, requires_grad = TRUE)
plastic <- torch_tensor(19.36, requires_grad = TRUE)
liquid <- torch_tensor(23.68, requires_grad = TRUE)
c100 <- torch_tensor(100.0, requires_grad = TRUE)

## plastic limit

n1 <- plastic - dry
n1$retain_grad()

n2 <- n1 / dry
n2$retain_grad()

Y <- n2 * c100

Y$backward()

results <- data.frame(nodes = c("n1","n2","Y"),
                      fwd = c(as.numeric(n1),
                              as.numeric(n2),
                              as.numeric(Y)),
                      part = c(abs(as.numeric(n1$grad)),
                               abs(as.numeric(n2$grad)),
                               1.0),
                      error = rep(rnd_error, 3))

fc <- results$error %*% results$part
pc <- 2 * fc

Y
fc
pc

## liquid limit
n1 <- liquid - dry
n1$retain_grad()

n2 <- n1 / dry
n2$retain_grad()

Y <- n2 * c100

Y$backward()

results <- data.frame(nodes = c("n1","n2","Y"),
                      fwd = c(as.numeric(n1),
                              as.numeric(n2),
                              as.numeric(Y)),
                      part = c(abs(as.numeric(n1$grad)),
                               abs(as.numeric(n2$grad)),
                               1.0),
                      error = rep(rnd_error, 3))

fc <- results$error %*% results$part
pc <- 2 * fc

Y
fc
pc

## plasticity index
n1 <- plastic - dry
n1$retain_grad()

n2 <- n1 / dry
n2$retain_grad()

n3 <- n2 * c100
n3$retain_grad()

n4 <- liquid - dry
n4$retain_grad()

n5 <- n4 / dry
n5$retain_grad()

n6 <- n5 * c100
n6$retain_grad()

Y <- n6 - n3

Y$backward()

results <- data.frame(nodes = c("n1","n2","n3","n4","n5","n6","Y"),
                      fwd = c(as.numeric(n1),
                              as.numeric(n2),
                              as.numeric(n3),
                              as.numeric(n4),
                              as.numeric(n5),
                              as.numeric(n6),
                              as.numeric(Y)),
                      part = c(abs(as.numeric(n1$grad)),
                               abs(as.numeric(n2$grad)),
                               abs(as.numeric(n3$grad)),
                               abs(as.numeric(n4$grad)),
                               abs(as.numeric(n5$grad)),
                               abs(as.numeric(n6$grad)),
                               1.0),
                      error = rep(rnd_error, 7))

fc <- results$part %*% results$error
pc <- 2*fc

Y
fc
pc

## calculate error for determining magnetic declination
cur_year <- torch_tensor(2026.0, requires_grad = TRUE)
ref_year <- torch_tensor(2016.0, requires_grad = TRUE)
ref_md_deg <- torch_tensor(-19.0, requires_grad = TRUE)
ref_md_min <- torch_tensor(-12.0, requires_grad = TRUE)
delta_deg <- torch_tensor(0, requires_grad = TRUE)
delta_min <- torch_tensor(-4, requires_grad = TRUE)
c60 <- torch_tensor(60.0, requires_grad = TRUE)


## convert reference md to dec
n1 <- ref_md_min / c60
n1$retain_grad()

n2 <- n1 + ref_md_deg
n2$retain_grad()

## calculate total change
n3 <- cur_year - ref_year
n3$retain_grad()

## convert change to dec
n4 <- delta_min / c60
n4$retain_grad()

n5 <- delta_deg + n4
n5$retain_grad()

## calculate total change
n6 <- n5 * n3
n6$retain_grad()

Y <- n2 + n6

Y$backward()

results <- data.frame(nodes = c("n1","n2","n3","n4","n5","n6","Y"),
                      fwd = c(as.numeric(n1),
                              as.numeric(n2),
                              as.numeric(n3),
                              as.numeric(n4),
                              as.numeric(n5),
                              as.numeric(n6),
                              as.numeric(Y)),
                      part = c(abs(as.numeric(n1$grad)),
                               abs(as.numeric(n2$grad)),
                               abs(as.numeric(n3$grad)),
                               abs(as.numeric(n4$grad)),
                               abs(as.numeric(n5$grad)),
                               abs(as.numeric(n6$grad)),
                               1.0),
                      error = c(rnd_error,
                                rnd_error,
                                0.0,
                                rnd_error,
                                rnd_error,
                                rnd_error,
                                rnd_error))

fc <- results$error %*% results$part
pc <- 2 * fc
Y
fc
pc

## Calculate magnetic forward bearing
cur_year <- torch_tensor(2026.0, requires_grad = TRUE)
ref_year <- torch_tensor(2016.0, requires_grad = TRUE)
ref_md_deg <- torch_tensor(-19.0, requires_grad = TRUE)
ref_md_min <- torch_tensor(-12.0, requires_grad = TRUE)
delta_deg <- torch_tensor(0, requires_grad = TRUE)
delta_min <- torch_tensor(-4, requires_grad = TRUE)
c60 <- torch_tensor(60.0, requires_grad = TRUE)
tfb <- torch_tensor(100.0, requires_grad = TRUE)


## convert reference md to dec
n1 <- ref_md_min / c60
n1$retain_grad()

n2 <- n1 + ref_md_deg
n2$retain_grad()

## calculate total change
n3 <- cur_year - ref_year
n3$retain_grad()

## convert change to dec
n4 <- delta_min / c60
n4$retain_grad()

n5 <- delta_deg + n4
n5$retain_grad()

## calculate total change
n6 <- n5 * n3
n6$retain_grad()

## calc new magnetic declination
n7 <- n2 + n6
n7$retain_grad()

## calculate magnetic forward bearing
Y <- tfb - n7

Y$backward()

results <- data.frame(nodes = c("tfb","n1","n2","n3",
                                "n4","n5","n6","n7","Y"),
                      fwd = c(as.numeric(tfb),
                              as.numeric(n1),
                              as.numeric(n2),
                              as.numeric(n3),
                              as.numeric(n4),
                              as.numeric(n5),
                              as.numeric(n6),
                              as.numeric(n7),
                              as.numeric(Y)),
                      part = c(abs(as.numeric(tfb$grad)),
                               abs(as.numeric(n1$grad)),
                               abs(as.numeric(n2$grad)),
                               abs(as.numeric(n3$grad)),
                               abs(as.numeric(n4$grad)),
                               abs(as.numeric(n5$grad)),
                               abs(as.numeric(n6$grad)),
                               abs(as.numeric(n7$grad)),
                               1.0),
                      error = c(ang_error,
                                rnd_error,
                                rnd_error,
                                0.0,
                                rnd_error,
                                rnd_error,
                                rnd_error,
                                rnd_error,
                                rnd_error))

fc <- results$error %*% results$part
pc <- 2 * fc
Y
fc
pc

## determine forward bearing given declination and
## magnetic backward bearing
md_deg <- torch_tensor(-8.0, requires_grad = TRUE)
md_min <- torch_tensor(-45.0, requires_grad = TRUE)
mbb <- torch_tensor(105.0, requires_grad = TRUE)
c60 <- torch_tensor(60.0, requires_grad = TRUE)
c180 <- torch_tensor(180.0, requires_grad = TRUE)

## convert md to dec
n1 <- md_min / c60
n1$retain_grad()

n2 <- md_deg + n1
n2$retain_grad()

## calc mfb
n3 <- mbb + c180
n3$retain_grad()

Y <- n3 + n2

Y$backward()

results <- data.frame(nodes = c("n1","n2","n3","Y"),
                      fwd = c(as.numeric(n1),
                              as.numeric(n2),
                              as.numeric(n3),
                              as.numeric(Y)),
                      part = c(abs(as.numeric(n1$grad)),
                               abs(as.numeric(n2$grad)),
                               abs(as.numeric(n3$grad)),
                               1.0),
                      error = c(rnd_error,
                                rnd_error,
                                rnd_error,
                                rnd_error))

fc <- results$error %*% results$part
pc <- 2 * fc
Y
fc
pc


## Determine ground distance Bryn -> Kelt
sb_dist <- torch_tensor(10000.0, requires_grad = TRUE)
sb_length <- torch_tensor(34.0, requires_grad = TRUE)
map_dist <- torch_tensor(55.0, requires_grad = TRUE)

n1 <- sb_dist / sb_length
n1$retain_grad()

Y <- n1 * map_dist

Y$backward()

results <- data.frame(nodes = c("sb_length", "n1", "Y"),
                      fwd = c(as.numeric(sb_length),
                              as.numeric(n1),
                              as.numeric(Y)),
                      part = c(abs(as.numeric(sb_length$grad)),
                               abs(as.numeric(n1$grad)),
                               1.0),
                      error = c(dist_error,
                                rnd_error,
                                rnd_error))

fc <- results$error %*% results$part
pc <- 2 * fc
Y
fc
pc

## length of irregular line
sb_length <- torch_tensor(34.0, requires_grad = TRUE)
sb_dist <- torch_tensor(10000.0, requires_grad = TRUE)
arc_interval <- torch_tensor(4000.0, requires_grad = TRUE)
remainder <- torch_tensor(8.0, requires_grad = TRUE)
num_arcs <- torch_tensor(6.0, requires_grad = TRUE)

## map scale factor (mm to m)
n1 <- sb_length / sb_dist
n1$retain_grad()

## compass interval in mm
n2 <- n1 * arc_interval
n2$retain_grad()

## ground dist scale factor (m to mm)

n3 <- sb_dist / sb_length
n3$retain_grad()

## ground distance of arc
n4 <- n2 * n3
n4$retain_grad()

## length based on arcs
n5 <- num_arcs * n4
n5$retain_grad()

## ground distance of remainder
n6 <- remainder * n3
n6$retain_grad()

## length of irregular line
Y <- n5 + n6

Y$backward()

results <- data.frame(nodes = c("sb_length","n1","n2","n3",
                                "n4","n5","n6","Y"),
                      fwd = c(as.numeric(sb_length),
                              as.numeric(n1),
                              as.numeric(n2),
                              as.numeric(n3),
                              as.numeric(n4),
                              as.numeric(n5),
                              as.numeric(n6),
                              as.numeric(Y)),
                      part = c(abs(as.numeric(sb_length$grad)),
                               abs(as.numeric(n1$grad)),
                               abs(as.numeric(n2$grad)),
                               abs(as.numeric(n3$grad)),
                               abs(as.numeric(n4$grad)),
                               abs(as.numeric(n5$grad)),
                               abs(as.numeric(n6$grad)),
                               1.0),
                      error = c(dist_error,
                                rnd_error,
                                (rnd_error + cmp_error),
                                rnd_error,
                                rnd_error,
                                rnd_error,
                                rnd_error,
                                rnd_error))

fc <- results$error %*% results$part
pc <- 2 * fc
Y
fc
pc
