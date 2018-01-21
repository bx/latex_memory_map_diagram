TARGET=example

$(TARGET).pdf: $(TARGET).tex sample.csv
	pdflatex --shell-escape $<
clean:
	rm $(TARGET).pdf $(TARGET).aux $(TARGET).log
