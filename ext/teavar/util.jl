using Distributions, DelimitedFiles, ProgressMeter, Combinatorics

####################################################################################
#######################  Print Results of TEAVAR formulation  ########################
####################################################################################

function printResults(o, alpha, a, u, umax, edges, scenarios, T, Tf, L, capacity, p, demand; verbose=false, utilization=true)
    println("Objective value: ", o)
    println("Alpha: ", alpha)
    print("\n")
    println("------------------ Allocations ----------------------\n")
    for i in 1:size(a,1)
    	println("Flow ", i, " demand= ", demand[i])
        for j in 1:size(a,2)
            println("Flow ",i, ", tunnel ", j, " allocated : ", a[i,j])
            print("Edges in use: ")
            for e in T[Tf[i][j]]
                print(edges[e])
            end
            println("\n")
        end
    end
    if verbose && false # too many scenarios in some cases
        println("--------------- Loss Breakdown ---------------------\n")
        for s in 1:size(umax,1)
            println("Scenario ", s, ": ", scenarios[s], " prob: ", p[s])
            print("Down edges: ")
            for i in 1:size(scenarios[s],1)
                if scenarios[s][i] == 0.0
                    print(edges[i], " ")
                end
            end
	    println("")

            for f in 1:size(u,2)
	        if u[s,f] > alpha
                    println("Loss on flow ", f, " = ", u[s,f]-alpha)
		end
            end
            println("umax[", s, "] = ", umax[s])
            println("\n")
        end
    end
    println("------------------Utilization-------------------\n")
    if utilization
        for e in 1:size(edges,1)
            s = 0
            for f in 1:size(a,1)
                for t in 1:size(a,2)
                    s += a[f,t] * L[Tf[f][t],e]
                end
            end
            print("EDGE values: ", e, " : ", edges[e], " cap: ", capacity[e], " alloc: ", s)
	    if s > 0.99 * capacity[e]
	    	print(" <-- near cap")
	    end
            println("")
        end
    end
    # writedlm("inputs/input3/allocations.txt", getvalue(a))
end


####################################################################################
###################  Compute all possible scenario bitmaps  ########################
####################################################################################

function kScenarios(nedges, k, probabilities; first=true)
    scenarios = []
    if first
        scenario = ones(nedges)
        push!(scenarios, scenario)
    end
    for i in 1:k
        for bits in collect(combinations(1:nedges,i))
            s = ones(nedges)
            for bit in bits
                s[bit] = 0
            end
            push!(scenarios, s)
        end
    end
    probs = getProbabilities(scenarios, probabilities)
    return scenarios, probs
end

function allScenarios(nedges, probabilities; first=true)
    scenarios = []
    probs = []
    if first
        scenario = ones(nedges)
        push!(scenarios, scenario) #ADD SCENARIO NO FAILURES
        prob = 1
        for i in 1:length(scenario)
            prob *= (1 - scenario[i]) * probabilities[i] + scenario[i] * (1 - probabilities[i])
        end
        push!(probs, prob)
    end
    p = Progress(nedges, .1, "Computing all scenarios...", 50)
    for i in 1:nedges
        for bits in collect(combinations(1:nedges,i))
            s = ones(nedges)
            for bit in bits
                s[bit] = 0
            end
            prob = 1
            for i in 1:length(s)
                prob *= (1 - s[i]) * probabilities[i] + s[i] * (1 - probabilities[i])
            end
            push!(probs, prob)
            push!(scenarios, s)
        end
        next!(p, showvalues = [(:edges,"$(i)/$(nedges)")])
    end
    return scenarios, probs ./ sum(probs)
end

####################################################################################
####################  Get probabilities of all scenarios  ##########################
####################################################################################

function getProbabilities(scenarios, probabilities)
    nscenarios = size(scenarios, 1)
    p = []
    for s in 1:nscenarios
        prob = 1
        for i in 1:size(scenarios[s],1)
            prob *= (1 - scenarios[s][i]) * probabilities[i] + scenarios[s][i] * (1 - probabilities[i])
        end
        push!(p, prob)
    end
    return p
end


####################################################################################
####################  Compute all scenarios above a threshold  #####################
####################################################################################

function subScenariosRecursion(original, cutoff, remaining=[], offset=0, partial=[], scenarios=[], probabilities=[]; progress=nothing)
    if (size(partial,1) == 0)   #first
        push!(scenarios, ones(size(original,1)))
        push!(probabilities, prod(1 .- original))
        remaining = original
    else (size(partial,1) > 0)
        probs = 1 .- original
        bitmap = ones(size(original, 1))   #create bitmap
        for index in partial
            probs[index] = original[index]
            bitmap[index] = 0
        end
        product = prod(probs)
        if progress != nothing
            ProgressMeter.next!(progress, showvalues = [(:cutoff,cutoff), (:scenarios_added,length(probabilities)), (:last, product)])
        end
        if product >= cutoff
            push!(scenarios, bitmap)
            push!(probabilities, product)
        else
            return
        end
    end
    yield()

    for i in 1:size(remaining,1)
        offset = size(original,1) - size(remaining,1)
        n = offset + i
        subScenariosRecursion(original, cutoff, remaining[i+1:end], offset, vcat(partial, [n]), scenarios, probabilities, progress=progress)
    end
    return scenarios, probabilities
end

function subScenarios(original, cutoff; first=true, last=true, progress=true)
    p = ProgressMeter.ProgressUnknown("Computing scenarios cutoff=$(cutoff)...")
    if progress
        scenarios, probabilities = subScenariosRecursion(original, cutoff, progress=p)
    else
        scenarios, probabilities = subScenariosRecursion(original, cutoff)
    end
    if first == false
        scenarios = scenarios[2:end]
        probabilities = probabilities[2:end]
    end
    if last
        push!(scenarios, zeros(length(scenarios[1])))
        push!(probabilities, 1 - sum(probabilities))
    end
    if sum(probabilities) < 1
        probabilities = probabilities ./ sum(probabilities)
    end
    ProgressMeter.finish!(p)
    return scenarios, probabilities
end

####################################################################################
####################  Weibull Distribution probabilities  #######################
####################################################################################

function weibullProbs(num; shape=.8, scale=.0001)
    w = Distributions.Weibull(shape, scale)
    probs = []
    for i in 1:num
        push!(probs, rand(w))
    end
    return probs
end


