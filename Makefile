PROJDIR := 'src'

help:
	@echo
	@echo 'make clean  - Removes all temporary server-build files (not ./bin)'
	@echo 'make server - Start lektor server with live change updates'
	@echo 'make build  - Build deployable website into ./bin'
	@echo 'make deploy - Custom rsync command to sync ./bin to remote server'
	@echo
	@echo 'make find-links - Search for cross reference between recipes'
	@echo

# Project build & clean

clean:
	@cd '$(PROJDIR)' && \
	temp_path="$$(lektor project-info --output-path)" && \
	if [[ -d "$$temp_path" ]]; then \
		echo "rm -rf $$temp_path"; rm -rf "$$temp_path"; \
	fi

server:
	@cd '$(PROJDIR)' && \
	(rm content/recipes; ln -s ../../data/development/ content/recipes) && \
	lektor server

build:
	@cd '$(PROJDIR)' && \
	(rm content/recipes; ln -s ../../data/distribution/ content/recipes) && \
	lektor build --output-path ../bin --buildstate-path ../build-state -f ENABLE_APPCACHE

deploy:
	@echo
	@echo 'Warning: This will not(!) build but sync all files in ./bin'
	@( read -p "Continue? [y/N]: " sure && case "$$sure" in [yY]) true;; *) false;; esac )
	@echo # --dry-run
	rsync -rclzv --exclude=.lektor --exclude=.DS_Store --delete bin/ vps:/srv/http/recipe-lekture

# Helper methods on all recipes

find-links:
	@echo
	@cd '$(PROJDIR)/content/recipes' && \
	find */*.lr -exec grep --color=auto -i ".\.\./[^ ]*" -o {} + \
	|| echo 'nothing found.'
	@echo
